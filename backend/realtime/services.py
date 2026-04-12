import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger("paper_trader.realtime")


def publish_event(channel_name: str, event_type: str, data: dict):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning("Channel layer not configured, skipping event publish")
        return

    logger.info(f"Publishing {event_type} to {channel_name}")
    try:
        async_to_sync(channel_layer.group_send)(
            channel_name,
            {
                "type": "event_message",
                "data": {
                    "type": event_type,
                    **data,
                },
            },
        )
        logger.info(f"Successfully published {event_type} to {channel_name}")
    except Exception:
        logger.exception("Failed to publish event to channel %s", channel_name)