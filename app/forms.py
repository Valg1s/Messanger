from django import forms
from phonenumber_field.formfields import PhoneNumberField


class LoginForm(forms.Form):
    phone_number = PhoneNumberField(label="Номер телефону",min_length=10, max_length=15)


class RegisterForm(forms.Form):
    first_name = forms.CharField(label="Ім'я",min_length=2,max_length=16)
    second_name = forms.CharField(label="Прізвище",min_length=2,max_length=16)
    phone_number = PhoneNumberField(label="Номер телефону", min_length=10, max_length=15)


class CheckSmsCodeForm(forms.Form):
    sms_code = forms.IntegerField(min_value=10000,max_value=99999,widget=forms.NumberInput)


class SearchForm(forms.Form):
    search_field = forms.CharField(label="Пошук",min_length=1,
                                   widget=forms.TextInput(attrs={"max-width":"fit-content",
                                                                 "placeholder": "Введі ім'я користувача,назву аккаунта"
                                                                                " користувача чи номер телефону"
                                                                                " з кодом країни"}))
