import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.sessions.models import Session

from app.models import CustomUser, Chat, Message


class ChatWebSocket(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = await self.get_user_id()
        await self.change_is_active(True)
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.change_is_active(False)
        await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        chat_id = data['chat_id']

        await self.add_message_to_chat(chat_id,message)

        recipient_id = await self.get_recipient_id(chat_id)

        await self.send_to_user(f"user_{recipient_id}", chat_id, message)

    async def send_to_user(self, recipient, chat_id, message):
        await self.channel_layer.group_send(recipient, {'type': 'send.message', 'message': message, 'chat_id': chat_id})

    async def send_message(self, event):
        message = event['message']
        chat_id = event['chat_id']
        await self.send(text_data=json.dumps({"chat_id": chat_id, 'message': message}))

    @sync_to_async
    def get_user_id(self):
        headers = dict(self.scope['headers'])
        cookie_header = headers[b'cookie'].decode('utf-8')
        cookies = cookie_header.split('; ')
        sessionid = None

        for cookie in cookies:
            if cookie.startswith('sessionid='):
                sessionid = cookie.split('=')[1]
                break

        session = Session.objects.get(session_key=sessionid)
        session_data = session.get_decoded()
        uid = session_data.get('_auth_user_id')
        user = CustomUser.objects.get(user_id=uid)

        return user.user_id

    @sync_to_async
    def get_recipient_id(self, chat_id):
        current_user = CustomUser.objects.get(user_id=self.user_id)
        chat = Chat.objects.get(chat_id=chat_id)
        recipient_id = chat.get_second_user(current_user)

        return recipient_id.user_id

    @sync_to_async
    def add_message_to_chat(self, chat_id, message_text):
        chat = Chat.objects.get(chat_id=chat_id)
        user = CustomUser.objects.get(user_id=self.user_id)

        message = Message.create(user, message_text)

        chat.messages.add(message.message_id)

    @sync_to_async
    def change_is_active(self, status):
        user = CustomUser.objects.get(user_id=self.user_id)
        user.is_active = status
        user.save()
