import json
from collections import defaultdict
from itertools import chain
from random import randint

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import get_connection, EmailMessage
from django.shortcuts import render, HttpResponse, Http404, redirect
from django.template.loader import render_to_string
from django.views import View

from .forms import UserForm
from .models import CustomUser, Chat
from .validators import CustomEmailValidator


def decode_request(request):
    body_unicode = request.body.decode('utf-8')
    received_json = json.loads(body_unicode)

    return received_json


def get_random_code(request: 'WSGIRequest') -> int:
    """
    This method create random code and add to session
    :param request:
    :return: int with 6 numbers
    """

    code = randint(100000, 1000000)

    request.session['code'] = code
    return code


def send_email_code(request, email) -> None:
    """
    This method send message with code
    :param request:
    :param email: user email
    :return: None
    """

    with get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS
    ) as connection:
        subject = 'Код для месенджера'
        code = get_random_code(request)
        message = f"Вітаємо! \n\n" \
                  f"Ваш код,для входу в аккаунт меседжера: {code} \n" \
                  f"Будь лакска, не повідомляйте цей код третім особам." \
                  f" Якщо ви не робили запит на код,то просто проігноруйте цей лист! \n\n" \
                  f"Дякуємо,з повагою \n" \
                  f"команда розробників месенджера."

        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        EmailMessage(subject, message, email_from, recipient_list, connection=connection).send()


def get_context_for_chat(current_user):
    user_chats = Chat.get_sorted_chats(current_user)

    chats = []

    for chat in user_chats:
        second_user = chat.get_second_user(current_user)

        message = chat.messages.last()
        last_message = "Повідомлень ще немає..."
        if message:
            last_message = message.text

        chats.append({
            "chat_id": chat.chat_id,
            "user": second_user,
            "last_message": last_message,
        })

    return chats


class RegisterUserView(View):
    def post(self, request):
        received_json = decode_request(request)

        form = UserForm(received_json)

        if form.is_valid():
            request.session['registered_data'] = {
                "first_name": received_json["first_name"],
                "last_name": received_json["last_name"],
                "account_name": received_json["account_name"],
                "email": received_json["email"],
            }

            send_email_code(request, received_json["email"])

            data = {
                "html": render_to_string("auth/check_code.html", request=request)
            }

            result = HttpResponse(json.dumps(data), content_type='application/json')
        else:
            result = HttpResponse(json.dumps(form.errors), content_type='application/json', status=400)

        return result


class CheckUserAccountView(View):
    def post(self, request):
        email = decode_request(request)['email']

        if request.session.get("registered_data"):
            request.session.remove("registered_data")

        email_validator = CustomEmailValidator()

        try:
            email_validator(email)
        except ValidationError as e:
            data = {
                "message": e.message,
            }
            result = HttpResponse(json.dumps(data), content_type='application/json', status=400)
        else:
            user = authenticate(request, email=email)

            request.session['email'] = email

            if user:
                send_email_code(request, email)

                context = {
                    "email": email,
                }

                data = {
                    "page": "check",
                    "html": render_to_string("auth/check_code.html", request=request, context=context)
                }
            else:
                data = {
                    "page": "registration",
                    "html": render_to_string("auth/reg.html", request=request)
                }

            result = HttpResponse(json.dumps(data), content_type='application/json')

        return result


class SendEmailView(View):
    def post(self, request):
        email = decode_request(request)['email']
        send_email_code(request, email)

        return HttpResponse()


class LoginUserView(View):
    def post(self, request):
        code = decode_request(request)['code']
        sended_code = str(request.session['code'])

        if code == sended_code:
            user_data = request.session.get('registered_data')

            if user_data:
                new_user = CustomUser.objects.create(first_name=user_data['first_name'],
                                                     last_name=user_data['last_name'],
                                                     account_name=user_data['account_name'], email=user_data['email'])

                new_user.save()

                email = new_user.email

            else:
                email = request.session['email']

            user = authenticate(request, email=email)

            login(request, user)

            result = HttpResponse()
        else:
            result = HttpResponse(status=400)

        return result


class AuthenticationView(View):
    def get(self, request):
        return render(request, "auth/login.html")


class MessangerView(View):
    def get(self, request):
        context = {
            "chats": get_context_for_chat(request.user),
        }

        return render(request, "main/index.html", context=context)


class ChatView(View):
    def get(self, request, chat_id):
        current_user = request.user

        chat = Chat.objects.filter(chat_id=chat_id, users=current_user).first()

        if not chat:
            return Http404

        messages_by_date = defaultdict(list)

        for message in chat.messages.all():
            date = message.date_of_sending.date()
            messages_by_date[date].append(message)

        messages_by_day = list(messages_by_date.values())
        second_user = chat.get_second_user(current_user)

        context = {
            "chats": get_context_for_chat(current_user),
            "second_user": second_user,
            "messages_by_day": messages_by_day
        }

        return render(request, "main/chat.html", context=context)


class PeopleSearchView(View):
    def post(self, request):
        search_input = decode_request(request)['search_input']

        account_name_search = CustomUser.objects.filter(account_name__startswith=search_input)
        first_name_search = CustomUser.objects.filter(first_name__startswith=search_input)
        last_name_search = CustomUser.objects.filter(last_name__startswith=search_input)

        data = {"users": []}
        for user in chain(account_name_search, first_name_search, last_name_search):
            data["users"].append(
                {
                    "user_id": user.user_id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "user_account_name": user.account_name,
                }
            )

        return HttpResponse(json.dumps(data), content_type='application/json')


class CreateChatView(View):
    def get(self,request,user_id):
        try:
            second_user = CustomUser.objects.get(pk=user_id)
        except:
            return redirect("index")

        chat = Chat.create(request.user, second_user)

        return redirect("chat",chat_id=chat.chat_id)