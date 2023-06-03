from django.test import TestCase

from .models import CustomUser, Message , Chat
# Create your tests here.


class CustomUserTestCase(TestCase):
    """
    TestCase for Custom User database model
    """

    def setUp(self):
        """
        On this method create two users ,before all tests
        :return: None
        """

        self.user1 = CustomUser.objects.create(email='testuser1@example.com',
                                               first_name='Test',
                                               last_name='User1',
                                               account_name='@testuser1',
                                               photo=None)
        self.user2 = CustomUser.objects.create(email='testuser2@example.com',
                                               first_name='Test',
                                               last_name='User2',
                                               account_name=None,
                                               photo=None)

    def test_user_creation(self):
        """
        Method for check creation users
        :return:  None
        """

        self.assertIsInstance(self.user1, CustomUser)
        self.assertIsInstance(self.user2, CustomUser)

    def test_user_attributes(self):
        """
        Method for check all wrote attributes
        :return: None
        """

        self.assertEqual(self.user1.email, 'testuser1@example.com')
        self.assertEqual(self.user1.first_name, 'Test')
        self.assertEqual(self.user1.last_name, 'User1')
        self.assertEqual(self.user1.account_name, '@testuser1')
        self.assertIsNone(self.user2.account_name)
        self.assertTrue(self.user1.is_active)
        self.assertFalse(self.user1.is_staff)

    def test_user_string_representation(self):
        """
        Method for check __str__ method
        :return: None
        """

        self.assertEqual(str(self.user1), '@testuser1')
        self.assertEqual(str(self.user2), 'Test User2')


class MessageTestCase(TestCase):
    """
    TestCase for Message database model
    """

    def setUp(self):
        """
        On this method create user and message ,before all tests
        :return: None
        """

        self.user1 = CustomUser.objects.create(email='testuser1@example.com',
                                               first_name='Test',
                                               last_name='User1',
                                               account_name='@testuser1',
                                               photo=None)

        self.message = Message.create(self.user1, "Hello!")

    def test_message_creation(self):
        """
        Method for check creation message
        :return:  None
        """

        count = len(Message.objects.all())

        self.assertEqual(count, 1)

    def test_message_attributes(self):
        """
        Method for check all wrote attributes
        :return: None
        """

        self.assertEqual(self.message.user, self.user1)
        self.assertEqual(self.message.text, "Hello!")
        self.assertIsNotNone(self.message.date_of_sending)


class ChatTestCase(TestCase):
    """
    TestCase for Chat database model
    """

    def setUp(self):
        """
        On this method create user and message ,before all tests
        :return: None
        """

        self.user_1 = CustomUser.objects.create(email='testuser1@example.com',
                                               first_name='Test',
                                               last_name='User1',
                                               account_name='@testuser1',
                                               photo=None)

        self.user2 = CustomUser.objects.create(email='testuser2@example.com',
                                               first_name='Test',
                                               last_name='User2',
                                               account_name=None,
                                               photo=None)

        self.message = Message.create(user=self.user_1, text="Hello")
        self.chat = Chat.create(user_1=self.user_1 , user_2=self.user2)

    def test_chat_creation(self):
        """
        Method for check creation message
        :return:  None
        """

        self.assertIsInstance(self.chat, Chat)

    def test_chat_add_messages(self):
        """
        Method for check adding message
        :return: None
        """

        self.chat.messages.add(self.message)

    def test_chat_attributes(self):
        """
        Method for check all wrote attributes
        :return: None
        """

        self.assertIsNotNone(self.chat.users.all())
        self.assertIsNotNone(self.chat.messages.all())