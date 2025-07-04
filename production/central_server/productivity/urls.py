# urls.py
from django.urls import path
from .views import register_device, unregister_device, get_device_credentials

urlpatterns = [
    path("register", register_device),
    path("unregister", unregister_device),
    path("token", get_device_credentials),

]
