from django import forms
from phonenumber_field.formfields import PhoneNumberField

class LoginForm(forms.Form):
    phone_number = PhoneNumberField(label="Номер телефону",min_length=10, max_length=15)


class RegisterForm(forms.Form):
    first_name = forms.CharField(label="Ім'я",min_length=2,max_length=16)
    last_name = forms.CharField(label="Прізвище",min_length=2,max_length=16)
    phone_number = PhoneNumberField(label="Номер телефону", min_length=10, max_length=15)


class CheckSmsCodeForm(forms.Form):
    sms_code = forms.IntegerField(min_value=10000,max_value=99999,widget=forms.NumberInput)




