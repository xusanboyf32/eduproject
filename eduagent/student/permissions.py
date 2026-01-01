
from rest_framework import permissions
class IsStudent(permissions.BasePermission):
    """Talaba vazifani topshiradi va video ko'radi"""

    message = "Faqat studentlar bu amalni bajarishi mumkin."
    def has_permission(self, request, view):
        # Anonymous foydalanuvchi darhol rad etilsin
        if not request.user or not request.user.is_authenticated:
            return False


        # superuser har doim true shunda superuser ham student pagega ham kira oladi
        if request.user.is_superuser:
            return True


        # student uchun tekshiruv
        return hasattr(request.user, 'student_profile')

