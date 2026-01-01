
from rest_framework import permissions
from .models import Group

class IsSifatchi(permissions.BasePermission):
    """Faqat sifatchilar uchun"""
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        return hasattr(request.user, 'sifatchi_profile')

# ----------------  NEW ASSISTANT TEACHER PERMISSION -----------------------

# permissions.py
# course/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAssistantTeacherOrSuperAdmin(BasePermission):
    """
    - SuperAdmin: GET, PUT, PATCH (hamma profil)
    - Assistant Teacher: GET, PUT, PATCH (faqat o'zi)
    - POST, DELETE: hech kimga yo‘q
    """

    def has_permission(self, request, view):
        # POST va DELETE butunlay yopiq
        if request.method in ['POST', 'DELETE']:
            return False

        # Faqat login bo‘lganlar
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # SuperAdmin hammasiga ruxsat
        if request.user.is_superuser:
            return True

        # Assistant Teacher faqat o‘z profiliga
        return hasattr(request.user, 'assistant_teacher_profile') and obj.user == request.user



# --------------------- NEW HIGH TEACHER PERMISSION  ---------------------
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsHighTeacherOrReadOnly(BasePermission):
    """
    GET → superadmin va high teacher o'zini ko'rishi mumkin
    PUT/PATCH → faqat high teacher o'zini tahrirlashi mumkin
    POST/DELETE → API orqali umuman taqiqlangan
    """
    def has_permission(self, request, view):
        # GET/HEAD/OPTIONS → faqat login foydalanuvchilar
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated

        # PUT/PATCH → faqat high teacher
        if request.method in ['PUT', 'PATCH']:
            return hasattr(request.user, 'high_teacher_profile')

        # Boshqa metodlar (POST/DELETE) → taqiqlangan
        return False

# --------------------------------------------------------




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



# IsGroupMember ---> yangi versiyada yozdim toliq pro ishlashi uchun

# ----------------------------- ISGROUOMEMBER -------------------------------------
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedReadOnly(BasePermission):
    """
    Faqat login foydalanuvchilar GET qila oladi.
    POST / PUT / PATCH / DELETE API’da umuman yopiq.
    """
    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False
        return bool(request.user and request.user.is_authenticated)

# ------------------------------------------------------------------------------------------


# -----------------  NEW COURSE PERMISSION NEW VERSION --------------------------

from rest_framework.permissions import BasePermission

class IsAuthenticatedReadOnly(BasePermission):
    """
    Faqat login bo'lgan foydalanuvchilar GET (read-only) qila oladi.
    POST/PUT/DELETE mutlaqo yopiq.
    """
    def has_permission(self, request, view):
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return False
        return bool(request.user and request.user.is_authenticated)

# -------------------------------------------------------------------------------


# ---------------- YANGI NOTION PEMRISION ---------------------
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsTeacherOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        return (
            user.is_superuser or
            hasattr(user, 'high_teacher_profile') or
            hasattr(user, 'assistant_teacher_profile')
        )

# -----------------------------------------------------------------------


# ----------------------- TEACHER COMMENT YOZISH UCHUN -----------------------

from rest_framework import permissions


class IsAssistantTeacherOrAdmin(permissions.BasePermission):
    """
    Permission:
    - GET: SuperAdmin (barchasi), Assistant Teacher (faqat o'zi)
    - PUT, PATCH: SuperAdmin (barchasi), Assistant Teacher (faqat o'zi)
    - POST, DELETE: Hech kimga (faqat admin panel)
    """

    def has_permission(self, request, view):
        # Faqat autentifikatsiyadan o'tganlar
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # SuperAdmin: GET, PUT, PATCH
        if request.user.is_superuser:
            return True

        # Assistant Teacher: faqat o'z profiliga GET, PUT, PATCH
        if hasattr(request.user, 'assistant_teacher_profile'):
            return obj.user == request.user

        return False




class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Comment faqat yozgan assistant teacher yoki admin tahrirlashi mumkin
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Admin har doim CRUD qilishi mumkin
        if request.user.is_superuser:
            return True
        # Assistant teacher faqat o'z yozgan commentiga ruxsat
        return obj.assistant_teacher.user == request.user



#  KINESCOPE UCHUN VIDEO YUKLASH

from rest_framework.permissions import BasePermission

class IsSuperAdminOrSifatchiReadOnly(BasePermission):
    def has_permission(self, request, view):
        # faqat GET
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return False

        user = request.user
        if not user or not user.is_authenticated:
            return False

        # SuperAdmin
        if user.is_superuser:
            return True

        # Sifatchi
        if hasattr(user, 'sifatchi_profile'):
            return True

        return False



# NOTION UCHUN
from rest_framework.permissions import BasePermission

class IsAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        # faqat GET so'rovlarga ruxsat
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return False

        # faqat login bo'lganlar
        return bool(request.user and request.user.is_authenticated)







