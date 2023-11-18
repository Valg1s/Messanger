from django.urls import re_path
from django.contrib.auth.decorators import login_required

from . import views, consumers

urlpatterns = [
    re_path(r'^$', login_required(views.MessangerView.as_view(), login_url='/auth/')),
    re_path(r'^auth/$', views.AuthenticationView.as_view()),
    re_path(r'^check_user_account/', views.CheckUserAccountView.as_view()),
    re_path(r'^register_user/', views.RegisterUserView.as_view()),
    re_path(r'^login_user/', views.LoginUserView.as_view()),
    re_path(r'^(?P<chat_id>\d+)/$', views.ChatView.as_view()),
    re_path(r'send_code/', views.SendEmailView.as_view()),
    #re_path(r'^ws/chat/$', consumers.ChatWebSocket.as_asgi())
]