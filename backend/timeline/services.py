import uuid

from .models import TimelineEvent


def create_timeline_event(*, portfolio_id, event_type: str, description: str, metadata: dict | None = None) -> TimelineEvent:
    event = TimelineEvent.objects.create(
        portfolio_id=portfolio_id,
        event_type=event_type,
        description=description,
        metadata=metadata or {},
    )

    from realtime.services import publish_event

    publish_event(
        f"portfolio_{portfolio_id}",
        "portfolio.updated",
        {"event_type": event_type, "event_id": str(event.id), "portfolio_id": str(portfolio_id)},
    )

    return event


def create_notification_event(*, user_id, portfolio_id, event_type: str, description: str, metadata: dict | None = None) -> TimelineEvent:
    event = create_timeline_event(
        portfolio_id=portfolio_id,
        event_type=event_type,
        description=description,
        metadata=metadata,
    )

    from realtime.services import publish_event

    publish_event(
        f"user_{user_id}",
        "notification.created",
        {"event_type": event_type, "event_id": str(event.id)},
    )

    return event