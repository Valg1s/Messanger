from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self,first_name,second_name,phone_number):
        user = self.model(first_name=first_name,second_name=second_name,phone_number=phone_number)

        user.save(using= self._db)
        return user


class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=16,null=False,blank=False,verbose_name="Ім'я")
    second_name = models.CharField(max_length=16,null=False,blank=False,verbose_name="Прізвище")
    account_name = models.CharField(max_length=32, unique=True,null=True,blank=True,verbose_name="Назва аккаунту")
    phone_number = PhoneNumberField(blank=False,unique=True,verbose_name="Номер телефону")
    email = models.EmailField(blank=True,null=True,unique=True,verbose_name="Email")

    created_at = models.DateTimeField(editable=False, auto_now=timezone.now())
    updated_at = models.DateTimeField(auto_now=timezone.now())
    is_active = models.BooleanField(default=False, verbose_name="Є активним?")
    is_staff = models.BooleanField(default=False, verbose_name="Має доступ до адмін панелі?")
    is_superuser = models.BooleanField(default=False, verbose_name="Є суперюзером?")

    USERNAME_FIELD = "phone_number"

    objects = UserManager()

    class Meta:
        unique_together = ("first_name","second_name",)

    def __str__(self):
        return f"{self.account_name if self.account_name else self.second_name + ' ' + self.first_name }"

    def __repr__(self):
        return f"{self.__class__.__name__}:{self.user_id}"


    @staticmethod
    def create(first_name,second_name,phone_number):

        if 2 > len(first_name) or len(first_name) > 16 or 2 > len(second_name) or len(second_name) > 16:
            raise Exception("First name or second name invalid")

        if not phone_number:
            raise Exception("Invalid phone number")

        user = User(first_name=first_name,second_name=second_name,phone_number=phone_number)
        user.save()

        return user

    def update(self,first_name = None, second_name = None,account_name = None,phone_number = None,email = None ):
        if first_name:
            if 2 < len(first_name) < 16:
                self.first_name = first_name
            else:
                raise Exception("Invalid first name")

        if second_name:
            self.second_name = second_name

        if account_name:
            self.account_name = account_name

        if phone_number:
            self.phone_number = phone_number

        if email:
            self.email = email

        self.save()

        return True

    @staticmethod
    def get_by_id(id):
        return User.objects.filter(user_id=id).first()

    @staticmethod
    def find_by_name(first_name,second_name):
        user = User.objects.filter(first_name=first_name,second_name=second_name).first()

        return user

    @staticmethod
    def find_by_account_name(account_name):
        user = User.objects.filter(account_name=account_name).first()

        return user

    @staticmethod
    def find_by_phone_number(phone_number):
        user = User.objects.filter(phone_number=phone_number).first()

        return user

    @staticmethod
    def delete_by_id(id):
        User.objects.filter(user_id=id).delete()

        return True

    @staticmethod
    def get_all():
        return User.objects.all()


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_sender = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name="Message_User")
    message_text = models.CharField(max_length=1024)
    message_date = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return f"{self.message_text}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.message_id})"

    @staticmethod
    def create(user, text):
        message = None
        if user and text:
            message = Message(message_sender=user,message_text=text)
            message.save()

        return message

    def update(self, text):
        if text:
            self.message_text = text
            self.save()

        return True

    @staticmethod
    def delete_by_id(id):
        Message.objects.filter(message_id=id).delete()

        return None


class Chat(models.Model):
    chat_id = models.AutoField(primary_key=True)
    user = models.ManyToManyField(User,related_name="Chat_User",
                                  blank=False,null=False)
    message = models.ManyToManyField(Message,related_name="Chat_Message",null=True)

    def __str__(self):
        users = map(lambda x: str(x) ,self.user.all())

        return ",".join(users)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.chat_id})"

    def add_users(self,users):
        for user in users:
            self.user.add(user)

        self.save()

    def add_user(self,user):
        self.user.add(user)

        self.save()

    def add_message(self,message):
        self.message.add(message)

        self.save()

    def take_name(self, current_user):
        name = ""
        for user in self.user.all():
            if user.user_id != current_user.user_id:
                name += str(user)

        return name

    @staticmethod
    def get_by_id(id):
        return Chat.objects.filter(chat_id=id).first()

    @staticmethod
    def create(users):
        chat = Chat()
        chat.save()

        chat.add_users(users)

        return chat


