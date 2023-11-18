from django.forms import ModelForm

from .models import CustomUser


class UserForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "account_name", "email"]
