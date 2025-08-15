import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PurchaseStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join a group named after the purchase UUID
        self.purchase_uuid = self.scope['url_route']['kwargs']['purchase_uuid']
        self.room_group_name = f'purchase_{self.purchase_uuid}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # This function is called when a message is sent to the group
    async def purchase_update(self, event):
        # Send message data to the WebSocket
        await self.send(text_data=json.dumps({
            'status': event['status'],
            'html': event['html']
        }))