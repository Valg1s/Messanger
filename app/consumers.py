import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.sessions.models import Session
from app.models import CustomUser, Chat


class ChatWebSocket(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = await self.get_user_id()

        await self.channel_layer.group_add(f"user_{self.user_id}",self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_id, self.channel_name)
        await self.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        chat_id = data['chat_id']

        recipient_id = await self.get_recipient_id(chat_id)

        await self.send_to_user(f"user_{recipient_id}", message)

    async def send_to_user(self, recipient, message):
        recipient_channel = await self.get_recipient_channel(recipient)
        if recipient_channel:
            await self.channel_layer.send(recipient_channel, {'type': 'send.message', 'message': message})

    async def get_recipient_channel(self, recipient):
        return await self.channel_layer.group_channels(recipient).get()

    async def send_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({'message': message}))

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

        return recipient_id