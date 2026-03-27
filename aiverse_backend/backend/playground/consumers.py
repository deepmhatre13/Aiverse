import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class PlaygroundTrainingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket: /ws/playground/{experiment_id}/?token=...
    Sends per-epoch updates: {epoch, loss, accuracy}
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not getattr(self.user, "is_authenticated", False):
            await self.close(code=4001)
            return

        self.experiment_id = int(self.scope["url_route"]["kwargs"]["experiment_id"])
        ok = await self._user_can_access(self.experiment_id, self.user.id)
        if not ok:
            await self.close(code=4003)
            return

        self.group_name = f"playground_{self.experiment_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def training_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    @database_sync_to_async
    def _user_can_access(self, experiment_id: int, user_id: int) -> bool:
        from playground.models import Experiment
        return Experiment.objects.filter(id=experiment_id, user_id=user_id).exists()

