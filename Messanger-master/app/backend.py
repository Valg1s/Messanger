from django.contrib.auth.backends import BaseBackend
from django.core.validators import validate_email

from app.models import CustomUser


class CustomBackend:
    """
    Custom backend for a Custom User
    """
    def authenticate(self, request, email=None):
        """
        Custom authenticate,take email and return user
        if this email is exist in database
        :param request:
        :param email: valid email
        :return: user or None
        """
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return None
        else:
            return user

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return None