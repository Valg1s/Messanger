import base64
import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from cryptography.fernet import Fernet
from django.contrib.sessions.models import Session

from Messanger.settings import STATIC_URL, SECRET_KEY
from app.models import CustomUser, Chat, Message

invalid_chars = ['^', '%', '#', '@', '&', '!', '$', '(', ')']

secret_key = "".join(char for char in SECRET_KEY if char not in invalid_chars)

key = base64.urlsafe_b64encode(secret_key[-32:].encode("utf-8"))

fer = Fernet(key)


class ChatWebSocket(AsyncJsonWebsocketConsumer):
    """
    WebSocket class
    """
    async def connect(self) -> None:
        """
        Connection to WebSocket
        :return:
        """

        self.user_id = await self.get_user_id()
        await self.change_is_active(True)
        await self.channel_layer.group_add(f"user_{self.user_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code) -> None:
        """
        Disconnect from WebSocket
        :return:
        """
        await self.change_is_active(False)
        await self.channel_layer.group_discard(f"user_{self.user_id}", self.channel_name)
        await self.close()

    async def receive(self, text_data: str) -> None:
        """
        Receive text data to group
        :param text_data: str user message
        :return:
        """

        data = json.loads(text_data)
        message = data['message'].strip()

        if len(message) not in range(1, 513):
            return

        if not message:
            return

        chat_id = data['chat_id']
        fullname, photo = await self.get_addition_data()

        await self.add_message_to_chat(chat_id, message)

        recipient_id = await self.get_recipient_id(chat_id)

        await self.send_to_user(f"user_{recipient_id}", chat_id, message, fullname, photo)

    async def send_to_user(self, recipient, chat_id, message, fullname, photo):
        """
        Send message to group of users
        :param recipient: User
        :param chat_id: int chat id
        :param message: str user message
        :return:
        """
        await self.channel_layer.group_send(recipient, {'type': 'send.message', 'message': message, 'chat_id': chat_id,
                                                        'fullname': fullname, "photo": photo})

    async def send_message(self, event: dict) -> None:
        """
        Send json message
        :param event: dict with data
        :return:
        """

        message = event['message']
        chat_id = event['chat_id']
        fullname = event['fullname']
        photo = event['photo']

        await self.send(
            text_data=json.dumps({"chat_id": chat_id, 'message': message, 'fullname': fullname, "photo": photo}))

    @sync_to_async
    def get_user_id(self) -> int:
        """
        Get session id from cookies and get user id by session id
        :return: user id
        """

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
    def get_recipient_id(self, chat_id: int) -> int:
        """
        Gt recipient id by chat id
        :param chat_id: int chat id
        :return: int recipient id
        """

        current_user = CustomUser.objects.get(user_id=self.user_id)
        chat = Chat.objects.get(chat_id=chat_id)
        recipient_id = chat.get_second_user(current_user)

        return recipient_id.user_id

    @staticmethod
    def encrypt_message(message):
        return fer.encrypt(message.encode('utf-8'))

    @sync_to_async
    def add_message_to_chat(self, chat_id: int, message_text: str) -> None:
        """
        Save message into db
        :param chat_id: int chat id
        :param message_text: str user message
        :return:
        """

        chat = Chat.objects.get(chat_id=chat_id)
        user = CustomUser.objects.get(user_id=self.user_id)

        message_text = self.encrypt_message(message_text)

        message = Message.create(user, message_text.decode("utf-8"))

        chat.messages.add(message.message_id)

    @sync_to_async
    def change_is_active(self, status: bool) -> None:
        """
        change user status into db
        :param status: bool user active status
        :return:
        """

        user = CustomUser.objects.get(user_id=self.user_id)
        user.is_active = status
        user.save()

    @sync_to_async
    def get_addition_data(self):
        user = CustomUser.objects.get(user_id=self.user_id)
        username = f"{user.first_name} {user.last_name}"

        if user.photo:
            photo = user.photo
        else:
            photo = STATIC_URL + "images/user.png"

        return username, str(photo)
