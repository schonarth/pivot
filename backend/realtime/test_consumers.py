from unittest.mock import AsyncMock, MagicMock

import pytest

from realtime.consumers import PortfolioConsumer


@pytest.mark.asyncio
async def test_portfolio_consumer_joins_repair_group():
    consumer = PortfolioConsumer()
    consumer.scope = {"user": MagicMock(id="user-123", is_anonymous=False)}
    consumer.channel_name = "channel-1"
    consumer.channel_layer = MagicMock()
    consumer.channel_layer.group_add = AsyncMock()
    consumer.accept = AsyncMock()

    await consumer.connect()

    consumer.channel_layer.group_add.assert_any_await("user_user-123", "channel-1")
    consumer.channel_layer.group_add.assert_any_await("ohlcv_backfill", "channel-1")
    consumer.channel_layer.group_add.assert_any_await("ohlcv_repair", "channel-1")
    consumer.accept.assert_awaited_once()
