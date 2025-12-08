# # course/permissions.py
# from rest_framework import permissions
# from authentication.models import SifatchiProfile
# from course.models import Assistant_Teacher
#
# class IsSifatchi(permissions.BasePermission):
#     """Faqat sifatchi yuklashi mumkin"""
#     def has_permission(self, request, view):
#         return hasattr(request.user, 'sifatchi_profile')
#
# class IsAssistantTeacher(permissions.BasePermission):
#     """Faqat yordamchi ustoz baholashi mumkin"""
#     def has_permission(self, request, view):
#         return hasattr(request.user, 'assistant_teacher_profile')
#
# class IsHighTeacher(permissions.BasePermission):
#     """ Head teacher hamma narsani read qila oladi """
#     def has_permission(self, request, view):
#         return hasattr(request.user, 'high_teacher_profile')


##########################################################

from rest_framework import permissions
from .models import Group

class IsSifatchi(permissions.BasePermission):
    """Faqat sifatchilar uchun"""
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'sifatchi_profile')


class IsAssistantTeacher(permissions.BasePermission):
    """Faqat yordamchi ustozlar uchun"""

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'assistant_teacher_profile')


class IsHighTeacher(permissions.BasePermission):
    """Faqat katta ustozlar uchun"""

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'high_teacher_profile')


class CanUploadVideo(permissions.BasePermission):
    """Video yuklash huquqi - faqat sifatchi"""

    def has_permission(self, request, view):
        if view.action == 'create':
            return hasattr(request.user, 'sifatchi_profile')
        return True


class CanReviewTask(permissions.BasePermission):
    """Vazifani tekshirish huquqi - faqat yordamchi ustoz"""

    def has_permission(self, request, view):
        if view.action in ['review', 'partial_update', 'update']:
            return hasattr(request.user, 'assistant_teacher_profile')
        return True


class IsTaskOwner(permissions.BasePermission):
    """Vazifa egasimi?"""

    def has_object_permission(self, request, view, obj):
        # Talaba faqat o'z vazifasini ko'ra oladi
        if hasattr(request.user, 'student_profile'):
            return obj.student == request.user.student_profile
        return False


class IsGroupMember(permissions.BasePermission):
    """Guruh a'zosimi?"""

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Talaba o'z guruhidagi videolarni ko'ra oladi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return obj.group.filter(id=student.group.id).exists()

        # Yordamchi ustoz o'z guruhlaridagi videolarni ko'ra oladi
        if hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            groups = Group.objects.filter(assistant_teacher=assistant)
            return obj.group.filter(id__in=groups).exists()

        # Katta ustoz o'z guruhlaridagi videolarni ko'ra oladi
        if hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            groups = Group.objects.filter(main_teacher=high_teacher)
            return obj.group.filter(id__in=groups).exists()

        return False


# course boyicha permisison
class CourseAdd(permissions.BasePermission):
    """
       Foydalanuvchi:
       - Superuser bo'lsa, hamma CRUD mumkin
       - Sifatchi bo'lsa, hamma CRUD mumkin
       - Boshqalar faqat o'qishi mumkin (GET, HEAD, OPTIONS)
       """

    def has_permission(self, request, view):
        # Superuser bo'lsa hamma narsa mumkin
        if request.user.is_superuser:
            return True

        # Boshqalar faqat safe methods (GET, HEAD, OPTIONS)
        from rest_framework.permissions import SAFE_METHODS
        if request.method in SAFE_METHODS:
            return True

        # Qolganlar hech narsa qila olmaydi (POST, PUT, DELETE)
        return False

