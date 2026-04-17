import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("paper_trader.realtime")


class PortfolioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info(
            f"WebSocket connect attempt - user: {self.scope['user']}, "
            f"is_anonymous: {self.scope['user'].is_anonymous}"
        )
        if self.scope["user"].is_anonymous:
            logger.warning("Rejecting anonymous WebSocket connection")
            await self.close()
            return

        self.user_id = str(self.scope["user"].id)
        self.user_group = f"user_{self.user_id}"
        self.backfill_group = "ohlcv_backfill"
        self.repair_group = "ohlcv_repair"
        self.portfolio_groups = set()

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.backfill_group, self.channel_name)
        await self.channel_layer.group_add(self.repair_group, self.channel_name)
        logger.info(f"WebSocket connected for user {self.user_id}")
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        await self.channel_layer.group_discard(self.backfill_group, self.channel_name)
        await self.channel_layer.group_discard(self.repair_group, self.channel_name)
        for group in self.portfolio_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data=None):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            logger.info(f"WebSocket received: {action}")

            if action == "subscribe_portfolio":
                portfolio_id = data.get("portfolio_id")
                if portfolio_id:
                    group = f"portfolio_{portfolio_id}"
                    logger.info(f"Subscribing user {self.user_id} to {group}")
                    await self.channel_layer.group_add(group, self.channel_name)
                    self.portfolio_groups.add(group)
                    logger.info(f"Successfully subscribed to {group}")

            elif action == "unsubscribe_portfolio":
                portfolio_id = data.get("portfolio_id")
                group = f"portfolio_{portfolio_id}"
                if group in self.portfolio_groups:
                    logger.info(f"Unsubscribing user {self.user_id} from {group}")
                    await self.channel_layer.group_discard(group, self.channel_name)
                    self.portfolio_groups.discard(group)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received on WebSocket")

    async def event_message(self, event):
        logger.info(f"Sending event to client: {event['data'].get('type')}")
        await self.send(text_data=json.dumps(event["data"]))
