# from django.contrib import admin
# from .models import Student
#
# admin.site.register(Student)
#

# =====================================================
# =====================================================

# from django.contrib import admin
# from .models import Student
#
# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     readonly_fields = ('user',)
#     exclude = ('user',)
#
#
 # ==================================================
 # ==================================================
from django.contrib import admin
from .models import Student
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'assigned_group']  # guruhni ko'rsatish
    list_filter = ['assigned_group']  # guruh bo'yicha filtr
    search_fields = ['full_name', 'phone']
    readonly_fields = ('user',)
