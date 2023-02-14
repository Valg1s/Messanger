from random import randrange

from django.shortcuts import render, redirect
import sms

from .forms import LoginForm, RegisterForm, CheckSmsCodeForm
from .models import User


# Create your views here.
def send_message(message, number):
    with sms.get_connection() as connection:
        sms.Message(message,
                    '+13152843237',
                    [number],
                    connection=connection).send()


def check_auth(request):
    if request.user.is_authenticated:
        return render(request, "main.html")
    else:
        return redirect("auth:login")


def register(request):
    phone_number = request.session.get("phone_number", None)

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            phone_number = str(form.cleaned_data["phone_number"])

            security_code = randrange(10000, 99999, 1)

            message = f'Добрий день, {first_name} {last_name}, ви ввели цей номер при реєстрації.' \
                      f' Ваш код: {security_code}. Не повідомляйте цей код третім особам.Якщо ви не' \
                      f' реєструвалися,просто ігноруйте це повідомлення'

            send_message(message, phone_number)

            request.session["user_data"] = {"first_name": first_name, "last_name": last_name,
                                            "phone_number": phone_number, "security_code": security_code,
                                            "priv_page": "auth:register"}

            return redirect("auth:check_sms_code")
    else:
        if phone_number:
            form = RegisterForm({'phone_number': phone_number})
        else:
            form = RegisterForm()

    context = {"form": form}
    return render(request, "auth/register.html", context=context)


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            phone_number = str(form.cleaned_data["phone_number"])

            user = User.objects.filter(phone_number=phone_number).first()

            if user:
                security_code = randrange(10000, 99999, 1)
                message = f"Добрий день, {user.first_name} {user.second_name}. Ваш код авторизації {security_code}"

                #send_message(message, phone_number)
                print(message)

                request.session["user_data"] = {"user_id": user.user_id, "security_code": security_code,
                                                "phone_number": phone_number, "priv_page": "auth:login"}

                return redirect("auth:check_sms_code")

            else:
                request.session["phone_number"] = phone_number

                return redirect('auth:register')
    else:
        form = LoginForm()

    context = {"form": form}
    return render(request, "auth/login_check_number.html", context=context)


def check_sms_code(request):
    user_data = request.session.get("user_data", None)

    if user_data:
        if request.method == "POST":
            form = CheckSmsCodeForm(request.POST)

            if form.is_valid():
                sms_code = form.cleaned_data["sms_code"]

                if sms_code == user_data["security_code"]:
                    print("Код зівпав")
                    if user_data["priv_page"] == "auth:login":
                        pass
                        #login
                    else:
                        pass
                        #register
                else:
                    form.add_error("sms_code","Ви ввели неправильний код")

        else:
            form = CheckSmsCodeForm()

        context = {
            "form": form,
            "phone_number": user_data["phone_number"],
        }

        return render(request, "auth/check_sms_code.html", context=context)

    else:
        return redirect("auth:login")
