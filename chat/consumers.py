import json
from datetime import datetime

import jwt
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.serializers.json import DjangoJSONEncoder

from chat.models import Messages
from EduTrack import settings
from EduTrack.utils import get_or_not_found
from users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_params = self.scope.get("query_string", b"").decode("utf-8")
        token = query_params.split("token=")[-1] if "token=" in query_params else None

        if not token:
            print("No token provided")
            await self.close(code=4001)
            return

        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            self.sender_id = decoded_token.get("user_id")
            if not self.sender_id:
                print("Invalid token: No user ID found")
                await self.close(code=3000)
                return

            self.receiver_id = self.scope["url_route"]["kwargs"].get("receiver_id")

            if not self.receiver_id:
                print("No receiver ID provided")
                await self.close(code=4002)
                return

            self.room_name = (
                f"chat_{min(int(self.sender_id), int(self.receiver_id))}"
                f"_{max(int(self.sender_id), int(self.receiver_id))}"
            )
            await self.channel_layer.group_add(self.room_name, self.channel_name)

            await self.accept()
            print(f"WebSocket connection established: {self.room_name}")

        except jwt.ExpiredSignatureError:
            print("Token has expired")
            await self.close(code=4004)
        except jwt.InvalidTokenError:
            print("Invalid token")
            await self.close(code=4005)
        except Exception as e:
            print(f"Unexpected error in WebSocket connection: {e}")
            await self.close(code=4006)

    async def disconnect(self, close_code):
        if self.room_name:
            await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        id = await self.save_message(message)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": message,
                "sender_id": self.sender_id,
                "message_id": id,
            },
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "content": event["message"],
                    "sender": event["sender_id"],
                    "created_at": datetime.now(),
                    "id": event["message_id"],
                },
                cls=DjangoJSONEncoder,
            )
        )

    @database_sync_to_async
    def save_message(self, content):
        sender = get_or_not_found(User.objects.all(), id=self.sender_id)
        receiver = get_or_not_found(User.objects.all(), id=self.receiver_id)

        test = Messages.save_message(sender=sender, receiver=receiver, content=content)
        return test.id
