from decimal import Decimal

from django.conf import settings


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

    publish_event(f"portfolio:{portfolio.id}", "portfolio.updated", {"portfolio_id": str(portfolio.id)})
    publish_event(f"user:{user.id}", "portfolio.updated", {"portfolio_id": str(portfolio.id), "user_id": str(user.id)})

    return {
        "portfolio": portfolio,
        "transaction": CashTransaction.objects.filter(portfolio=portfolio).first(),
        "snapshot": PortfolioSnapshot.objects.filter(portfolio=portfolio).first(),
    }


def deposit(*, portfolio, amount: Decimal) -> dict:
    from .models import CashTransaction, PortfolioSnapshot

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
        f"portfolio:{portfolio.id}", "cash.updated", {"portfolio_id": str(portfolio.id), "transaction_type": "deposit"}
    )

    return {"transaction": transaction, "snapshot": snapshot}


def withdraw(*, portfolio, amount: Decimal) -> dict:
    from .models import CashTransaction, PortfolioSnapshot

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
        f"portfolio:{portfolio.id}",
        "cash.updated",
        {"portfolio_id": str(portfolio.id), "transaction_type": "withdrawal"},
    )

    clamped = actual_amount < amount

    return {"transaction": transaction, "snapshot": snapshot, "clamped": clamped, "actual_amount": actual_amount}


def _create_snapshot(portfolio) -> "PortfolioSnapshot":
    from trading.models import Position
    from .models import PortfolioSnapshot

    positions_value = Decimal("0")
    positions = Position.objects.filter(portfolio=portfolio).select_related("asset")
    for pos in positions:
        from markets.quote_provider import get_latest_quote

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
    from trading.models import Position
    from markets.quote_provider import get_latest_quote

    positions = Position.objects.filter(portfolio=portfolio).select_related("asset")
    positions_value = Decimal("0")
    position_details = []

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
            }
        )

    total_equity = portfolio.current_cash + positions_value
    net_flows = _calculate_net_external_cash_flows(portfolio)
    trading_pnl = total_equity - net_flows

    return {
        "portfolio_id": str(portfolio.id),
        "name": portfolio.name,
        "market": portfolio.market,
        "base_currency": portfolio.base_currency,
        "initial_capital": str(portfolio.initial_capital),
        "current_cash": str(portfolio.current_cash),
        "positions_value": str(positions_value),
        "total_equity": str(total_equity),
        "net_external_cash_flows": str(net_flows),
        "trading_pnl": str(trading_pnl),
        "positions": position_details,
    }


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