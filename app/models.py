from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    """
    This is Custom Manager for Custom User,
    used for create new interface for creating Custom User
    """

    def create_user(self, email: str, first_name: str, last_name: str, account_name=None,
                    **extra_fields) -> 'CustomUser':
        """
        Used for create Custom User using custom fields
        :param email: user email
        :param first_name: first name of user
        :param last_name: last name of user
        :param account_name: short account name , for easier searching
        :param extra_fields: something extra
        :return: instance of Custom User class
        """

        if not email:
            raise ValueError('The Email field must be set')
        if account_name and not account_name.startswith('@'):
            account_name = '@' + account_name
        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            account_name=account_name,
            **extra_fields
        )
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    """
    Database model for custom users.
    Save all info about user account
    """

    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    account_name = models.CharField(max_length=50, unique=True, null=True,blank=True)
    email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='media/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'account_name'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.account_name or f"{self.first_name} {self.last_name}"


class Message(models.Model):
    """
    Database model for messages.
    Save all information about message user,
    message text , date and time of sending
    """

    message_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.CharField(max_length=512)
    date_of_sending = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message {self.message_id} from {self.user}'

    @staticmethod
    def create(user: 'CustomUser', text: str) -> 'Message':
        """
        This method create and save message,
        that user was wrote
        :param user: instance of CustomUser
        :param text: string with message
        :return: instance of Message
        """

        message = Message.objects.create(user=user, text=text, date_of_sending=timezone.now())

        message.save()

        return message


class Chat(models.Model):
    """
    Database model for chats.
    Save information about chat users and all messages
    """

    chat_id = models.AutoField(primary_key=True)
    users = models.ManyToManyField(CustomUser)
    messages = models.ManyToManyField(Message)

    @staticmethod
    def get_sorted_chats(user):
        chats = Chat.objects.filter(users=user) \
            .annotate(last_message_date=models.Max('messages__date_of_sending')) \
            .order_by(models.F('last_message_date').desc(nulls_last=True))

        return chats

    # @property
    # def last_message_date(self):
    #     return self.messages.aggregate(models.Max('date_of_sending')).get('date_of_sending__max')

    def __str__(self):
        return f'Chat {self.chat_id}'

    @staticmethod
    def create(user_1: 'CustomUser', user_2: 'CustomUser') -> 'Chat':
        """
        This method based on Multiton pattern.
        If chat with given users is exist return that,
        If not create new, and return
        :param: user_1: instance of CustomUser
        :param: user_2: instance of CustomUser
        :return: instance of Chat
        """

        existing_chat = Chat.objects.filter(users= user_1).filter(users= user_2).first()

        if not existing_chat:
            existing_chat = Chat.objects.create()

            existing_chat.users.add(user_1, user_2)

            existing_chat.save()

        return existing_chat

    def get_second_user(self, first_user: 'CustomUser') -> 'CustomUser':
        """
        Take user, check all users in current chat,and return second user
        :param first_user: user who open main page
        :return: CustomUser
        """
        users = self.users.all()

        for user in users:
            if user.user_id != first_user.user_id:
                return user


class Reaction(models.Model):
    """
    Database model for reactions.
    Save all information about user,who react on message,
    what message and name of reaction
    """

    reaction_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    name_of_reaction = models.CharField(max_length=50, default='like')

    def __str__(self):
        return f'{self.user} reacted with {self.name_of_reaction} to message {self.message}'

    @staticmethod
    def create(user: 'CustomUser', message: 'Message') -> 'None':
        """
        This method create reaction on message
        :param user: instance of CustomUser
        :param message: instance of Message
        :return: None
        """

        reaction = Reaction.objects.create(user=user, message=message)

        reaction.save()
