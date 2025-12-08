# from rest_framework.permissions import BasePermission
#
# class IsOperatorOrAdmin(BasePermission):
#     """Namunaviy permission: kerak bo'lsa kengaytirasiz."""
#     def has_permission(self, request, view):
#         role = getattr(getattr(request, "user", None), "role", None)
#         return role in ["admin", "operator"]
#



# from rest_framework.permissions import BasePermission, SAFE_METHODS
#
# class IsHighTeacherOrReadOnly(BasePermission):
#     """
#     High Teacher barcha resurslarda to'liq CRUD qilish mumkin,
#     boshqalar faqat read-only.
#     """
#     def has_permission(self, request, view):
#         user = request.user
#         if not user.is_authenticated:
#             return False
#         if user.role == 'high_teacher':
#             return True
#         # Boshqalar uchun faqat read-only
#         return request.method in SAFE_METHODS
#
# class IsAssistantTeacherOrReadOnly(BasePermission):
#     """
#     Assistant Teacher faqat o'ziga biriktirilgan talabalar va chatlarni ko'radi,
#     boshqa foydalanuvchilar read-only.
#     """
#     def has_object_permission(self, request, view, obj):
#         user = request.user
#         if not user.is_authenticated:
#             return False
#
#         if user.role == 'high_teacher':
#             return True  # High Teacher uchun full access
#
#         if user.role == 'assistant_teacher':
#             # Talabani o'ziga biriktirilgan bo'lsa
#             if hasattr(obj, 'assigned_assistant_teacher'):
#                 return obj.assigned_assistant_teacher and obj.assigned_assistant_teacher.user == user
#             # ChatMessage bo'lsa
#             if hasattr(obj, 'student'):
#                 return obj.student.assigned_assistant_teacher and obj.student.assigned_assistant_teacher.user == user
#
#         # Boshqalar uchun read-only
#         return request.method in SAFE_METHODS
#
# class IsStudentSelfOrReadOnly(BasePermission):
#     """
#     Talaba faqat o'z profilini ko'rishi mumkin.
#     Boshqa talabalarni yoki resurslarni o'zgartira olmaydi.
#     """
#     def has_object_permission(self, request, view, obj):
#         user = request.user
#         if not user.is_authenticated:
#             return False
#
#         if user.role == 'student':
#             return obj.user == user  # faqat o'zini ko'rishi mumkin
#
#         # High/Assistant teacher va admin uchun full access
#         if user.role in ['high_teacher', 'assistant_teacher', 'admin']:
#             return True
#
#         return request.method in SAFE_METHODS


from rest_framework import permissions
class IsStudent(permissions.BasePermission):
    """Talaba vazifani topshiradi va video ko'radi"""
    def has_permission(self, request, view):
        # superuser har doim true shunda superuser ham student pagega ham kira oladi
        if request.user.is_superuser:
            return True
        # student uchun tekshiruv
        return hasattr(request.user, 'student_profile')

