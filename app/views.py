from random import randrange

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
import sms

from .forms import LoginForm, RegisterForm, CheckSmsCodeForm, SearchForm, SendMessageForm
from .models import User, Chat, Message


# Create your views here.
@login_required(login_url="/login/")
def main(request):
    if request.method == "POST":
        form = SearchForm(request.POST)

        if form.is_valid():
            field = form.cleaned_data.get("search_field")

            name = field.split(' ')
            user = None
            users = None

            if len(name) == 2:
                user = User.objects.filter(first_name=name[0], second_name=name[1]).first() or \
                       User.objects.filter(first_name=name[1], second_name=name[0]).first()

            if not user:
                user = User.objects.filter(account_name=field).first() or \
                       User.objects.filter(phone_number=field).first()
                users = User.objects.filter(first_name=field).all() or \
                        User.objects.filter(first_name=field).all()

            if user:
                user_pare = [user, request.user]
                general_chats = Chat.objects.filter(user__in=user_pare).all()

                personal_chat = None

                if general_chats:
                    for chat in general_chats:
                        if len(chat.user.all()) == 2:
                            personal_chat = chat
                            break

                if not personal_chat:
                    personal_chat = Chat.create(user_pare)

                return redirect("messanger:chat", chat_id=personal_chat.chat_id)

            if users:
                request.session['users'] = users
                return

    else:
        form = SearchForm()

    user_id = request.user.user_id
    user = User.get_by_id(user_id)
    chats = Chat.objects.filter(user=user).all()

    result = []
    for chat in chats:
        last_message = chat.message.order_by("-message_id").first()

        result.append(
            {
                "chat_name": chat.take_name(user),
                "chat_id": chat.chat_id,
                "chat_last_message": last_message,
            }
        )

    context = {
        "form": form,
        "chats": result,
    }
    return render(request, "main.html", context=context)

def search_users(request):
    users = request.session.get('users',None)

    context = {
        "users": users,
    }




@login_required(login_url="/login/")
def chat(request, chat_id):
    cur_chat = Chat.get_by_id(chat_id)
    cur_user = request.user

    if cur_user in cur_chat.user.all():
        if request.method == "POST":
            form = SendMessageForm(request.POST)

            if form.is_valid():
                message_text = form.cleaned_data["message"]
                message = Message.create(cur_user, message_text)

                cur_chat.add_message(message)

        form = SendMessageForm()

        context = {
            "form": form,
            "chat_name": cur_chat.take_name(request.user),
            "messages": cur_chat.message.all()
        }
        return render(request, "chat.html", context)
    else:
        return redirect("messanger:main")


def send_message(message, number):
    with sms.get_connection() as connection:
        sms.Message(message,
                    '+13152843237',
                    [number],
                    connection=connection).send()


def register_user(request):
    phone_number = request.session.get("phone_number", None)

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data["first_name"]
            second_name = form.cleaned_data["second_name"]
            phone_number = str(form.cleaned_data["phone_number"])

            security_code = randrange(10000, 99999, 1)

            message = f'Добрий день, {first_name} {second_name}, ви ввели цей номер при реєстрації.' \
                      f' Ваш код: {security_code}. Не повідомляйте цей код третім особам.Якщо ви не' \
                      f' реєструвалися,просто ігноруйте це повідомлення'

            # send_message(message, phone_number)
            print(message)

            request.session["user_data"] = {"first_name": first_name, "second_name": second_name,
                                            "phone_number": phone_number, "security_code": security_code,
                                            "priv_page": "messanger:register"}

            return redirect("messanger:check_sms_code")
    else:
        if phone_number:
            form = RegisterForm({'phone_number': phone_number})
        else:
            form = RegisterForm()

    context = {"form": form}
    return render(request, "auth/register.html", context=context)


def login_user(request):
    print(request.user)
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            phone_number = str(form.cleaned_data["phone_number"])

            user = User.objects.filter(phone_number=phone_number).first()

            if user:
                security_code = randrange(10000, 99999, 1)
                message = f"Добрий день, {user.first_name} {user.second_name}. Ваш код авторизації {security_code}"

                # send_message(message, phone_number)
                print(message)

                request.session["user_data"] = {"user_id": user.user_id, "security_code": security_code,
                                                "phone_number": phone_number, "priv_page": "messanger:login"}

                return redirect("messanger:check_sms_code")

            else:
                request.session["phone_number"] = phone_number

                return redirect('messanger:register')
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

                    if user_data["priv_page"] == "messanger:login":
                        user_id = user_data.get("user_id")
                        user = User.get_by_id(user_id)
                    else:
                        first_name = user_data["first_name"]
                        second_name = user_data["second_name"]
                        phone_number = user_data["phone_number"]

                        user = User.create(first_name, second_name, phone_number)

                    user.is_active = True
                    user.save()

                    login(request, user)
                    return redirect("messanger:main")

                else:
                    form.add_error("sms_code", "Ви ввели неправильний код")

        else:
            form = CheckSmsCodeForm()

        context = {
            "form": form,
            "phone_number": user_data["phone_number"],
        }

        return render(request, "auth/check_sms_code.html", context=context)

    else:
        return redirect("messanger:login")


@login_required(login_url="/login/")
def logout_user(request):
    logout(request)

    return redirect("messanger:login")
