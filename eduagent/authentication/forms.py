from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(forms.ModelForm):
    """
    Admin panelda yangi foydalanuvchi yaratishda
    password1/password2 talab qilinmaydi.
    """
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'role', 'is_staff', 'is_active')

class CustomUserChangeForm(forms.ModelForm):
    """
    Foydalanuvchi ma'lumotlarini o'zgartirish uchun form
    """
    class Meta:
        model = CustomUser
        fields = ('phone_number', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'is_superuser')
