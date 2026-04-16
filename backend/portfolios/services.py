from decimal import Decimal

MARKET_CURRENCY_MAP = {
    "BR": "BRL",
    "US": "USD",
    "UK": "GBP",
    "EU": "EUR",
}


def derive_currency(market: str) -> str:
    return MARKET_CURRENCY_MAP.get(market, "USD")


def get_fee_rate(market: str) -> Decimal:
    from markets.services import MARKET_CONFIGS

    cfg = MARKET_CONFIGS.get(market)
    if cfg:
        return Decimal(cfg["fee_rate"])
    return Decimal("0")


def create_portfolio(*, user, name: str, market: str, initial_capital: Decimal) -> dict:
    from .models import CashTransaction, Portfolio, PortfolioSnapshot

    base_currency = derive_currency(market)
    is_first = not Portfolio.objects.filter(user=user).exists()

    portfolio = Portfolio(
        user=user,
        name=name,
        market=market,
        base_currency=base_currency,
        initial_capital=initial_capital,
        current_cash=initial_capital,
        is_primary=is_first,
    )
    portfolio.save()

    CashTransaction.objects.create(
        portfolio=portfolio,
        transaction_type="initial_funding",
        amount=initial_capital,
        resulting_cash=initial_capital,
    )

    PortfolioSnapshot.objects.create(
        portfolio=portfolio,
        cash=initial_capital,
        positions_value=Decimal("0"),
        total_equity=initial_capital,
        net_external_cash_flows=initial_capital,
    )

    from realtime.services import publish_event

    publish_event(f"portfolio_{portfolio.id}", "portfolio.updated", {"portfolio_id": str(portfolio.id)})
    publish_event(f"user_{user.id}", "portfolio.updated", {"portfolio_id": str(portfolio.id), "user_id": str(user.id)})

    return {
        "portfolio": portfolio,
        "transaction": CashTransaction.objects.filter(portfolio=portfolio).first(),
        "snapshot": PortfolioSnapshot.objects.filter(portfolio=portfolio).first(),
    }


def deposit(*, portfolio, amount: Decimal) -> dict:
    from .models import CashTransaction

    if amount <= 0:
        raise ValueError("Deposit amount must be positive")

    portfolio.current_cash += amount
    portfolio.save(update_fields=["current_cash", "updated_at"])

    transaction = CashTransaction.objects.create(
        portfolio=portfolio,
        transaction_type="deposit",
        amount=amount,
        resulting_cash=portfolio.current_cash,
    )

    snapshot = _create_snapshot(portfolio)

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{portfolio.id}", "cash.updated", {"portfolio_id": str(portfolio.id), "transaction_type": "deposit"}
    )

    return {"transaction": transaction, "snapshot": snapshot}


def withdraw(*, portfolio, amount: Decimal) -> dict:
    from .models import CashTransaction

    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive")

    actual_amount = min(amount, portfolio.current_cash)
    portfolio.current_cash -= actual_amount
    portfolio.save(update_fields=["current_cash", "updated_at"])

    transaction = CashTransaction.objects.create(
        portfolio=portfolio,
        transaction_type="withdrawal",
        amount=actual_amount,
        resulting_cash=portfolio.current_cash,
    )

    snapshot = _create_snapshot(portfolio)

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{portfolio.id}",
        "cash.updated",
        {"portfolio_id": str(portfolio.id), "transaction_type": "withdrawal"},
    )

    clamped = actual_amount < amount

    return {"transaction": transaction, "snapshot": snapshot, "clamped": clamped, "actual_amount": actual_amount}


def _create_snapshot(portfolio):
    from markets.quote_provider import get_latest_quote
    from .models import PortfolioSnapshot
    from trading.models import Position

    positions_value = Decimal("0")
    positions = Position.objects.filter(portfolio=portfolio).select_related("asset")
    for pos in positions:
        quote = get_latest_quote(str(pos.asset_id))
        if quote:
            positions_value += pos.quantity * quote.price

    net_flows = _calculate_net_external_cash_flows(portfolio)

    total_equity = portfolio.current_cash + positions_value

    return PortfolioSnapshot.objects.create(
        portfolio=portfolio,
        cash=portfolio.current_cash,
        positions_value=positions_value,
        total_equity=total_equity,
        net_external_cash_flows=net_flows,
    )


def _calculate_net_external_cash_flows(portfolio) -> Decimal:
    from .models import CashTransaction

    transactions = CashTransaction.objects.filter(portfolio=portfolio)
    total = Decimal("0")
    for tx in transactions:
        if tx.transaction_type in ("initial_funding", "deposit"):
            total += tx.amount
        elif tx.transaction_type == "withdrawal":
            total -= tx.amount
    return total


def get_portfolio_summary(portfolio) -> dict:
    from ai.services import AIService
    from markets.quote_provider import get_latest_quote
    from .models import PortfolioWatchMembership
    from trading.models import Position

    positions = Position.objects.filter(portfolio=portfolio).select_related("asset")
    positions_value = Decimal("0")
    position_details = []
    position_assets = []

    for pos in positions:
        quote = get_latest_quote(str(pos.asset_id))
        current_price = quote.price if quote else pos.average_cost
        market_value = pos.quantity * current_price
        unrealized_pnl = market_value - (pos.quantity * pos.average_cost)
        positions_value += market_value
        position_details.append(
            {
                "asset_id": str(pos.asset_id),
                "symbol": pos.asset.display_symbol,
                "name": pos.asset.name,
                "quantity": pos.quantity,
                "average_cost": pos.average_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "currency": pos.asset.currency,
                "position_detail": (
                    f"{pos.quantity} @ {current_price} | MV {market_value} | U P&L {unrealized_pnl}"
                ),
            }
        )
        position_assets.append(pos.asset)

    watch_memberships = PortfolioWatchMembership.objects.filter(portfolio=portfolio).select_related("asset")
    watch_details = []
    watch_assets = []
    for membership in watch_memberships:
        quote = get_latest_quote(str(membership.asset_id))
        watch_details.append(
            {
                "asset_id": str(membership.asset_id),
                "symbol": membership.asset.display_symbol,
                "name": membership.asset.name,
                "market": membership.asset.market,
                "currency": membership.asset.currency,
                "current_price": str(quote.price) if quote else None,
            }
        )
        watch_assets.append(membership.asset)

    total_equity = portfolio.current_cash + positions_value
    net_flows = _calculate_net_external_cash_flows(portfolio)
    trading_pnl = total_equity - net_flows

    scope_insights = {"portfolio": None, "watch": None}
    service = AIService(portfolio.user)
    if service.has_ai_enabled():
        try:
            if position_assets:
                scope_insights["portfolio"] = service.analyze_scope(
                    "portfolio",
                    f"{portfolio.name} positions",
                    position_assets,
                    position_details,
                )
        except Exception:
            scope_insights["portfolio"] = None

        try:
            if watch_assets:
                scope_insights["watch"] = service.analyze_scope(
                    "watch",
                    f"{portfolio.name} watch",
                    watch_assets,
                    watch_details,
                )
        except Exception:
            scope_insights["watch"] = None

    return {
        "portfolio_id": str(portfolio.id),
        "name": portfolio.name,
        "market": portfolio.market,
        "base_currency": portfolio.base_currency,
        "initial_capital": str(portfolio.initial_capital),
        "current_cash": str(portfolio.current_cash),
        "is_simulating": portfolio.is_simulating,
        "positions_value": str(positions_value),
        "total_equity": str(total_equity),
        "net_external_cash_flows": str(net_flows),
        "trading_pnl": str(trading_pnl),
        "positions": position_details,
        "watch_assets": watch_details,
        "scope_insights": scope_insights,
    }


def add_watch_asset(*, portfolio, asset) -> dict:
    from .models import PortfolioWatchMembership
    from realtime.services import publish_event

    if asset.market != portfolio.market:
        raise ValueError(f"Asset market {asset.market} does not match portfolio market {portfolio.market}")

    membership, created = PortfolioWatchMembership.objects.get_or_create(portfolio=portfolio, asset=asset)
    if created:
        publish_event(
            f"portfolio_{portfolio.id}",
            "portfolio.updated",
            {"portfolio_id": str(portfolio.id), "asset_id": str(asset.id), "watch_action": "add"},
        )
    return {"membership": membership, "created": created}


def remove_watch_asset(*, portfolio, asset) -> dict:
    from .models import PortfolioWatchMembership
    from realtime.services import publish_event

    deleted, _ = PortfolioWatchMembership.objects.filter(portfolio=portfolio, asset=asset).delete()
    if deleted:
        publish_event(
            f"portfolio_{portfolio.id}",
            "portfolio.updated",
            {"portfolio_id": str(portfolio.id), "asset_id": str(asset.id), "watch_action": "remove"},
        )
    return {"deleted": deleted > 0}


def calculate_twr(portfolio, snapshots=None) -> Decimal:
    from .models import PortfolioSnapshot

    if snapshots is None:
        snapshots = list(PortfolioSnapshot.objects.filter(portfolio=portfolio).order_by("captured_at"))

    if len(snapshots) < 2:
        return Decimal("0")

    twr = Decimal("1")
    for i in range(1, len(snapshots)):
        start = snapshots[i - 1]
        end = snapshots[i]

        flow_during_period = end.net_external_cash_flows - start.net_external_cash_flows

        if start.total_equity == 0:
            continue

        period_return = (end.total_equity - start.total_equity - flow_during_period) / start.total_equity
        twr *= (1 + period_return)

    return twr - 1
