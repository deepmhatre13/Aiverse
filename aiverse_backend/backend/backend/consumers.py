import json

from channels.generic.websocket import AsyncWebsocketConsumer


class TestWebSocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "message": "WebSocket connected",
                }
            )
        )

    async def disconnect(self, close_code):
        return

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None:
            await self.send(bytes_data=bytes_data)
            return

        payload = {}
        if text_data:
            try:
                payload = json.loads(text_data)
            except json.JSONDecodeError:
                payload = {"message": text_data}

        message = payload.get("message", "pong")
        await self.send(
            text_data=json.dumps(
                {
                    "type": "echo",
                    "message": message,
                }
            )
        )