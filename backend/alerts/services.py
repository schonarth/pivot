from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.utils import timezone

from .models import Alert, AlertTrigger


def evaluate_alert(alert: Alert, current_price: Decimal) -> AlertTrigger | None:
    matched = False
    if alert.condition_type == "price_above" and current_price > alert.threshold:
        matched = True
    elif alert.condition_type == "price_below" and current_price < alert.threshold:
        matched = True

    alert.last_evaluated_at = timezone.now()
    alert.save(update_fields=["last_evaluated_at", "updated_at"])

    if not matched:
        return None

    notification_sent = False
    trade = None
    outcome = "notification_only"

    if alert.notify_enabled:
        notification_sent = _send_notification(alert, current_price)

    if alert.auto_trade_enabled:
        trade, outcome = _execute_auto_trade(alert, current_price)

    if alert.notify_enabled and alert.auto_trade_enabled:
        if trade:
            outcome = "notification_and_trade_executed"
        elif outcome == "trade_skipped":
            outcome = "notification_and_trade_skipped"
        elif outcome == "trade_failed":
            outcome = "notification_and_trade_failed"
    elif not alert.notify_enabled and alert.auto_trade_enabled:
        pass

    trigger = AlertTrigger.objects.create(
        alert=alert,
        triggered_price=current_price,
        outcome=outcome,
        details={"threshold": str(alert.threshold), "condition_type": alert.condition_type, "price_at_trigger": str(current_price)},
        notification_sent=notification_sent,
        trade=trade,
    )

    alert.status = "triggered"
    alert.triggered_at = timezone.now()
    alert.save(update_fields=["status", "triggered_at", "updated_at"])

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{alert.portfolio_id}",
        "alert.triggered",
        {"alert_id": str(alert.id), "trigger_id": str(trigger.id), "portfolio_id": str(alert.portfolio_id)},
    )

    return trigger


def _send_notification(alert: Alert, current_price: Decimal) -> bool:
    from django.conf import settings

    if not alert.notify_enabled:
        return False

    from timeline.services import create_notification_event

    create_notification_event(
        user_id=alert.portfolio.user_id,
        portfolio_id=alert.portfolio_id,
        event_type="alert.notification",
        description=f"Alert triggered: {alert.condition_type} at {current_price} for {alert.asset.display_symbol}",
        metadata={
            "alert_id": str(alert.id),
            "condition_type": alert.condition_type,
            "threshold": str(alert.threshold),
            "current_price": str(current_price),
            "asset_symbol": alert.asset.display_symbol,
        },
    )
    return True


def _execute_auto_trade(alert: Alert, current_price: Decimal) -> tuple:
    from trading.services import execute_buy, execute_sell
    from trading.models import Position

    portfolio = alert.portfolio
    asset = alert.asset
    quantity = None
    side = alert.auto_trade_side
    outcome = "trade_failed"

    if alert.auto_trade_quantity is not None:
        quantity = alert.auto_trade_quantity
    elif alert.auto_trade_pct is not None:
        pct = alert.auto_trade_pct / Decimal("100")
        if side == "BUY":
            available_cash = portfolio.current_cash
            gross_possible = available_cash * pct
            price = current_price
            fee_rate = Decimal(str(__import__("portfolios.services", fromlist=["get_fee_rate"]).get_fee_rate(portfolio.market)))
            gross_with_fees = price * (1 + fee_rate)
            quantity = int((gross_possible / gross_with_fees).quantize(Decimal("1"), rounding=ROUND_DOWN))
        elif side == "SELL":
            try:
                position = Position.objects.get(portfolio=portfolio, asset=asset)
                quantity = int((Decimal(str(position.quantity)) * pct).quantize(Decimal("1"), rounding=ROUND_DOWN))
            except Position.DoesNotExist:
                return None, "trade_skipped"

    if quantity is None or quantity <= 0:
        return None, "trade_skipped"

    rationale = f"Auto-trade triggered by alert: {alert.condition_type} {alert.threshold}"

    try:
        if side == "BUY":
            result = execute_buy(portfolio=portfolio, asset=asset, quantity=quantity, rationale=rationale, executed_by="alert")
        else:
            result = execute_sell(portfolio=portfolio, asset=asset, quantity=quantity, rationale=rationale, executed_by="alert")
        return result["trade"], "trade_executed"
    except ValueError:
        return None, "trade_skipped"
    except Exception:
        return None, "trade_failed"