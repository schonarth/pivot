from decimal import Decimal, ROUND_HALF_EVEN

from django.db import transaction
from django.utils import timezone

from .models import Position, Trade
from markets.quote_provider import get_latest_quote
from portfolios.services import _create_snapshot, get_fee_rate


MINIMUM_ORDER_VALUE = Decimal("10")


def execute_buy(*, portfolio, asset, quantity: int, rationale: str = "Manual operation", executed_by: str = "manual") -> dict:
    if quantity <= 0:
        raise ValueError("Quantity must be a positive integer")

    from markets.models import Asset

    if asset.market != portfolio.market:
        raise ValueError(f"Asset market {asset.market} does not match portfolio market {portfolio.market}")

    quote = get_latest_quote(str(asset.id))
    if quote is None:
        from markets.quote_provider import refresh_asset_quote

        quote = refresh_asset_quote(str(asset.id))
        if quote is None:
            raise ValueError(f"No quote available for asset {asset.display_symbol}")

    price = quote.price
    gross_value = price * Decimal(quantity)
    fee_rate = get_fee_rate(portfolio.market)
    fees = (gross_value * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    net_cash_required = gross_value + fees

    if gross_value < MINIMUM_ORDER_VALUE:
        raise ValueError(f"Order value {gross_value} is below minimum order value of {MINIMUM_ORDER_VALUE}")

    with transaction.atomic():
        portfolio = portfolio.__class__.objects.select_for_update().get(pk=portfolio.pk)

        if portfolio.current_cash < net_cash_required:
            max_quantity = int((portfolio.current_cash - fees) / price) if fees < portfolio.current_cash else 0
            raise ValueError(
                f"Insufficient cash. You have {portfolio.current_cash}, but this trade requires {net_cash_required}.",
                {"available_cash": str(portfolio.current_cash), "required_cash": str(net_cash_required), "max_quantity": max_quantity},
            )

        position, created = Position.objects.select_for_update().get_or_create(
            portfolio=portfolio,
            asset=asset,
            defaults={"quantity": 0, "average_cost": Decimal("0")},
        )

        if created:
            position.quantity = quantity
            position.average_cost = (gross_value + fees) / Decimal(quantity)
        else:
            old_total_cost = position.average_cost * Decimal(position.quantity)
            new_total_quantity = Decimal(position.quantity + quantity)
            position.average_cost = (old_total_cost + gross_value + fees) / new_total_quantity
            position.quantity += quantity

        position.save(update_fields=["quantity", "average_cost", "updated_at"])

        portfolio.current_cash -= net_cash_required
        portfolio.save(update_fields=["current_cash", "updated_at"])

        trade = Trade.objects.create(
            portfolio=portfolio,
            asset=asset,
            action="BUY",
            quantity=quantity,
            price=price,
            gross_value=gross_value,
            fees=fees,
            net_cash_impact=-net_cash_required,
            realized_pnl=None,
            rationale=rationale,
            executed_by=executed_by,
        )

        snapshot = _create_snapshot(portfolio)

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{portfolio.id}",
        "trade.executed",
        {"trade_id": str(trade.id), "portfolio_id": str(portfolio.id), "action": "BUY"},
    )

    return {"trade": trade, "position": position, "snapshot": snapshot}


def execute_sell(*, portfolio, asset, quantity: int, rationale: str = "Manual operation", executed_by: str = "manual") -> dict:
    if quantity <= 0:
        raise ValueError("Quantity must be a positive integer")

    with transaction.atomic():
        portfolio = portfolio.__class__.objects.select_for_update().get(pk=portfolio.pk)

        try:
            position = Position.objects.select_for_update().get(portfolio=portfolio, asset=asset)
        except Position.DoesNotExist:
            raise ValueError(f"No position found for asset {asset.display_symbol} in this portfolio")

        if position.quantity < quantity:
            raise ValueError(
                f"Insufficient shares. You have {position.quantity}, but tried to sell {quantity}.",
                {"available_quantity": position.quantity, "requested_quantity": quantity},
            )

        quote = get_latest_quote(str(asset.id))
        if quote is None:
            from markets.quote_provider import refresh_asset_quote

            quote = refresh_asset_quote(str(asset.id))
            if quote is None:
                raise ValueError(f"No quote available for asset {asset.display_symbol}")

        price = quote.price
        gross_value = price * Decimal(quantity)
        fee_rate = get_fee_rate(portfolio.market)
        fees = (gross_value * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        net_proceeds = gross_value - fees
        cost_basis = position.average_cost * Decimal(quantity)
        realized_pnl = net_proceeds - cost_basis

        if gross_value < MINIMUM_ORDER_VALUE:
            raise ValueError(f"Order value {gross_value} is below minimum order value of {MINIMUM_ORDER_VALUE}")

        position.quantity -= quantity
        if position.quantity == 0:
            position.delete()
            position = None
        else:
            position.save(update_fields=["quantity", "updated_at"])

        portfolio.current_cash += net_proceeds
        portfolio.save(update_fields=["current_cash", "updated_at"])

        trade = Trade.objects.create(
            portfolio=portfolio,
            asset=asset,
            action="SELL",
            quantity=quantity,
            price=price,
            gross_value=gross_value,
            fees=fees,
            net_cash_impact=net_proceeds,
            realized_pnl=realized_pnl,
            rationale=rationale,
            executed_by=executed_by,
        )

        snapshot = _create_snapshot(portfolio)

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{portfolio.id}",
        "trade.executed",
        {"trade_id": str(trade.id), "portfolio_id": str(portfolio.id), "action": "SELL"},
    )

    return {"trade": trade, "position": position, "snapshot": snapshot, "realized_pnl": realized_pnl}