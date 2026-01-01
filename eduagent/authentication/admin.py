# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

# CustomUser admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ('phone_number', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('phone_number',)

    fieldsets = (
        (None, {'fields': ('phone_number',)}),
        ('Shaxsiy ma’lumot', {'fields': ('first_name', 'last_name', 'telegram_id', 'telegram_username')}),
        ('Rollar va huquqlar', {'fields': ( 'role', 'is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'role', 'is_staff', 'is_active')}

        ),
    )

# Admin panelga ro‘yxatga olish
admin.site.register(CustomUser, CustomUserAdmin)
