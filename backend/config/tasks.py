from celery import shared_task
import logging

logger = logging.getLogger("paper_trader.celery_tasks")


@shared_task
def capture_portfolio_snapshots():
    from portfolios.models import Portfolio
    from realtime.services import publish_event

    portfolios = Portfolio.objects.all()
    from portfolios.services import _create_snapshot

    for portfolio in portfolios:
        try:
            _create_snapshot(portfolio)
            publish_event(f"portfolio_{portfolio.id}", "price.updated", {"portfolio_id": str(portfolio.id)})
        except Exception:
            logger.exception("Failed to capture snapshot for portfolio %s", portfolio.id)


@shared_task
def send_email_notification(user_id: int, subject: str, message: str):
    from django.conf import settings
    from django.core.mail import send_mail

    if not settings.SMTP_ENABLED:
        logger.info("SMTP not configured, skipping email to user %s", user_id)
        return

    from accounts.models import User

    try:
        user = User.objects.get(id=user_id)
        send_mail(subject, message, None, [user.email])
    except Exception:
        logger.exception("Failed to send email to user %s", user_id)