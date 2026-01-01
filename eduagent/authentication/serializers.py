
# ==========================================================================================
#  SERIALIZER BOTDAN XABAR KELADIGAN QILIB
# ==========================================================================================

# authentication/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Vazifa: User ma'lumotlarini API ga chiqarish
    Natija: Frontend user haqida ma'lumot oladi
    """

    class Meta:
        model = CustomUser
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'role',
            'group', 'course', 'subject', 'is_verified', 'date_joined'
        ]
        read_only_fields = ['is_verified', 'date_joined']




