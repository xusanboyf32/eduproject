# authentication/permissions.py
from rest_framework.permissions import BasePermission

# BUnda ham login ham osha tegishli rolega ega bo'lishi kerak

# student oqiydi
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "student"

# chat qila oladi hamma bilan va hamma narsani kora di tahrirlaydi
class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "teacher"

# faqat oziga tegishli guruhlar bn chatlasha oladi
# class IsKurator(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == "kurator"
#
# # operator
class IsSifatchi(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'sifatchi'


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'superadmin'





