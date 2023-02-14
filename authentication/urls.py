from django.urls import re_path

from . import views

app_name = "auth"

urlpatterns = [
    #path('admin/', admin.site.urls),
    re_path(r"^$", views.check_auth),
    re_path(r"^login/$", views.login, name="login"),
    re_path(r"^register/$", views.register, name="register"),
    re_path(r"^check_sms_code/$", views.check_sms_code, name="check_sms_code")
]