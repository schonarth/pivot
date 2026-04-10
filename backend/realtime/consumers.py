import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger("paper_trader.realtime")


class PortfolioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_anonymous:
            await self.close()
            return

        self.user_id = str(self.scope["user"].id)
        self.user_group = f"user:{self.user_id}"
        self.portfolio_groups = set()

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group, self.channel_name)
        for group in self.portfolio_groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive(self, text_data=None):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "subscribe_portfolio":
                portfolio_id = data.get("portfolio_id")
                if portfolio_id:
                    group = f"portfolio:{portfolio_id}"
                    await self.channel_layer.group_add(group, self.channel_name)
                    self.portfolio_groups.add(group)

            elif action == "unsubscribe_portfolio":
                portfolio_id = data.get("portfolio_id")
                group = f"portfolio:{portfolio_id}"
                if group in self.portfolio_groups:
                    await self.channel_layer.group_discard(group, self.channel_name)
                    self.portfolio_groups.discard(group)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received on WebSocket")

    async def event_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))