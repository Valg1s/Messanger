import json
from collections import defaultdict
from random import randint

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import get_connection, EmailMessage
from django.shortcuts import render, HttpResponse, Http404, redirect
from django.template.loader import render_to_string
from django.views import View

from Messanger.settings import STATIC_URL
from .consumers import fer
from .forms import UserForm
from .models import CustomUser, Chat, Reaction, Message
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
    code = get_random_code(request)

    html_message = render_to_string("mail.html", {"code": code})

    with get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS
    ) as connection:
        subject = 'Код для месенджера'

        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        mail = EmailMessage(subject, html_message, email_from, recipient_list, connection=connection)
        mail.content_subtype = "html"
        mail.send()


def get_context_for_chat(current_user):
    user_chats = Chat.get_sorted_chats(current_user)

    chats = []

    for chat in user_chats:
        second_user = chat.get_second_user(current_user)

        message = chat.messages.last()
        last_message = "Повідомлень ще немає..."
        if message:
            last_message = decode_message(message.text)

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


def decode_message(message):
    return fer.decrypt(message.encode("utf-8")).decode("utf-8")


class ChatView(View):
    def get(self, request, chat_id):
        current_user = request.user

        chat = Chat.objects.filter(chat_id=chat_id, users=current_user).first()

        if not chat:
            return Http404

        messages_by_date = defaultdict(list)

        for message in chat.messages.all():
            date = message.date_of_sending.date()
            message.text = decode_message(message.text)
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

        users = []

        account_name_search = CustomUser.objects.filter(account_name__contains=search_input)

        users.extend(account_name_search)

        if len(users) < 3:
            first_name_search = CustomUser.objects.filter(first_name__contains=search_input)

            users.extend(first_name_search)

        if len(users) < 3:
            last_name_search = CustomUser.objects.filter(last_name__contains=search_input)

            users.extend(last_name_search)

        data = {"users": []}

        found_users = [request.user.user_id]

        for user in users:
            if user.user_id in found_users:
                continue

            data["users"].append(
                {
                    "user_id": user.user_id,
                    "user_name": f"{user.first_name} {user.last_name}",
                    "user_account_name": user.account_name,
                    "user_photo": user.photo or STATIC_URL + "images/user.png"
                }
            )

            found_users.append(user.user_id)

            if len(data["users"]) >= 3:
                break

        return HttpResponse(json.dumps(data), content_type='application/json')


class CreateChatView(View):
    def get(self, request, user_id):
        try:
            second_user = CustomUser.objects.get(pk=user_id)
        except:
            return redirect("index")

        chat = Chat.create(request.user, second_user)

        return redirect("chat", chat_id=chat.chat_id)


class MakeReactionView(View):

    def post(self, request):
        input_data = decode_request(request)

        user = CustomUser.objects.get(pk=int(input_data['user']))
        message = Message.objects.get(pk=input_data['message'])

        try:
            exist_reaction = Reaction.objects.get(user=user, message=message)

        except Reaction.DoesNotExist:
            Reaction.create(user, message)
        else:
            exist_reaction.delete()

        return HttpResponse(200)


class LogoutView(View):
    def post(self, request):
        try:
            user = CustomUser.objects.get(user_id=request.user.user_id)

            if not user.is_authenticated:
                raise ValueError
        except:
            return HttpResponse(status=400)
        else:
            logout(request)

            return redirect("auth")


class UpdateDataView(View):
    def post(self, request):
        try:
            user = CustomUser.objects.get(user_id=request.user.user_id)
        except:
            return HttpResponse(status=400)

        url = request.POST['url']
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        account_name = request.POST["account_name"]
        photo = request.FILES.get("photo")

        if first_name and first_name != user.first_name:
            user.first_name = first_name

        if last_name and last_name != user.last_name:
            user.last_name = last_name

        if account_name and account_name != user.account_name:
            try:
                CustomUser.objects.get(account_name=account_name)
            except:
                user.account_name = account_name

        if photo:
            user.photo = photo

        user.save()

        return redirect(url)


