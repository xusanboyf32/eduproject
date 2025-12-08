# authentication/urls.py
from django.urls import path
from .views import (
    TelegramLoginView, VerifyCodeView, CheckAuthView,
    LogoutView, AdminCreateUserView
)

urlpatterns = [
    # Kirish uchun
    path('telegram-login/', TelegramLoginView.as_view(), name='telegram-login'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Admin uchun
    path('admin/create-user/', AdminCreateUserView.as_view(), name='admin-create-user'),
]


