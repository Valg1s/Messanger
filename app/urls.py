from django.urls import re_path


from . import views

app_name = "messanger"

urlpatterns = [
    re_path(r"^$", views.main, name="main"),
    re_path(r"^chat/(?P<chat_id>\d+)$", views.chat, name="chat"),
    re_path(r"^search/$",views.search_users,name="search"),
    re_path(r"^login/$", views.login_user, name="login"),
    re_path(r"^register/$", views.register_user, name="register"),
    re_path(r"^check_sms_code/$", views.check_sms_code, name="check_sms_code"),
    re_path(r"^logout/$",views.logout_user, name="logout"),
]