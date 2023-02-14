import json

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.


class User(AbstractBaseUser):
    user_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=16,null=False,blank=False,verbose_name="Ім'я")
    second_name = models.CharField(max_length=16,null=False,blank=False,verbose_name="Прізвище")
    account_name = models.CharField(max_length=32, unique=True,null=True,blank=True,verbose_name="Назва аккаунту")
    phone_number = PhoneNumberField(blank=False,unique=True,verbose_name="Номер телефону")
    email = models.EmailField(blank=True,null=True,unique=True,verbose_name="Email")

    is_active = models.BooleanField(default=False, verbose_name="Є активним?")
    is_staff = models.BooleanField(default=False, verbose_name="Має доступ до адмін панелі?")
    is_superuser = models.BooleanField(default=False, verbose_name="Є суперюзером?")

    USERNAME_FIELD = "phone_number"

    class Meta:
        unique_together = ("first_name","second_name",)

    def __str__(self):
        return f"{self.user_id}|{self.second_name} {self.first_name}|{self.account_name if self.account_name else ' '}"

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

        return True

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
    def delete_by_id(id):
        User.objects.filter(user_id=id).delete()

        return True

    @staticmethod
    def get_all():
        return User.objects.all()

