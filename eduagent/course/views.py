
from .serializers import (
    KnescopeVideoUrlSerializer
)

from student.permissions import IsStudent




# ---------------  NEW COURSE VERISON VIEWS ------------------------------
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Course
from .serializers import CourseSerializer
from .permissions import IsAuthenticatedReadOnly

class CourseViewSet(ReadOnlyModelViewSet):
    """
    Course API - faqat GET, faqat login foydalanuvchilar.
    Foydalanuvchi faqat o'ziga tegishli kurslarni ko'radi.
    Admin panelda to'liq CRUD ishlaydi.
    """
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticatedReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        user = self.request.user

        # Superadmin va sifatchi → hamma kurslarni ko'radi
        if user.is_superuser or hasattr(user, 'sifatchi_profile'):
            return Course.objects.all()

        # High Teacher → faqat o'z kurslari
        if hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            return Course.objects.filter(group__main_teacher=high_teacher).distinct()

        # Assistant Teacher → faqat o'z kurslari
        if hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            return Course.objects.filter(group__assistant_teacher=assistant).distinct()

        # Talaba → faqat o'z kursi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return Course.objects.filter(group=student.group).distinct()

        # Boshqalar → hech narsa ko'rmaydi
        return Course.objects.none()


# ------------------------------------------------------------------------


from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import High_Teacher
from .serializers import HighTeacherSerializer

class HighTeacherViewSet(ReadOnlyModelViewSet):
    """
    High Teacher API:

    - High Teacher:
        * GET → faqat o‘z profilini ko‘radi
        * PATCH → faqat o‘z profilidagi ruxsat berilgan maydonlarni tahrirlashi mumkin
        * POST / DELETE → umuman yo‘q

    - Superadmin:
        * GET → barcha High Teacher profillarini ko‘radi
        * PATCH → barcha High Teacher profillarini tahrirlashi mumkin
    """
    serializer_class = HighTeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superadmin → barcha profillar
        if user.is_superuser:
            return High_Teacher.objects.all()

        # High Teacher → faqat o‘z profili
        if hasattr(user, 'high_teacher_profile'):
            return High_Teacher.objects.filter(user=user)

        # Boshqalar → hech narsa ko‘rmaydi
        return High_Teacher.objects.none()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        allowed_fields = [
            'full_name', 'date_of_birth', 'gender',
            'email', 'job', 'experience_year', 'info_knowladge', 'image'
        ]

        # Superadmin → barcha profillarni tahrirlashi mumkin
        if user.is_superuser:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # High Teacher → faqat o‘z profilini tahrirlashi mumkin
        if hasattr(user, 'high_teacher_profile') and instance.user == user:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        return Response(
            {"detail": "You do not have permission to edit this profile."},
            status=403
        )

# --------------------------------- ASSISTANT TEACHER NEW VERSION ---------------------------------
# course/views.py
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response

from .models import Assistant_Teacher
from .serializers import AssistantTeacherSerializer

class AssistantTeacherViewSet(ReadOnlyModelViewSet):
    """
    Assistant Teacher API:

    - GET → Superadmin barcha profillar, Assistant Teacher faqat o‘z profili
    - PATCH → Superadmin barcha profillar, Assistant Teacher faqat o‘z profili va ruxsat berilgan maydonlar
    - POST / DELETE → umuman ko‘rinmaydi
    """
    serializer_class = AssistantTeacherSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superadmin – barcha profillarni ko‘radi
        if user.is_superuser:
            return Assistant_Teacher.objects.all()

        # Assistant Teacher – faqat o‘z profilini ko‘radi
        if hasattr(user, 'assistant_teacher_profile'):
            return Assistant_Teacher.objects.filter(user=user)

        # Boshqalar – hech narsa ko‘rmaydi
        return Assistant_Teacher.objects.none()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        allowed_fields = [
            'full_name', 'date_of_birth', 'email',
            'job', 'experience_year', 'info_knowladge', 'image'
        ]

        # Superadmin → barcha maydonlar tahrir qilishi mumkin
        if user.is_superuser:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # Assistant Teacher → faqat o‘z profilidagi ruxsat etilgan maydonlar
        if hasattr(user, 'assistant_teacher_profile') and instance.user == user:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        return Response(
            {"detail": "You do not have permission to edit this profile."},
            status=403
        )



# --------------  DENY ALL yozildi xavfsizlik uchun hechkimga ruxsat yoq degani

from rest_framework.permissions import BasePermission
class DenyAllPermission(BasePermission):  # ✅ REUSABLE CLASS
    def has_permission(self, request, view):
        return False
# ------------------------- ------------------------------------------
from rest_framework.viewsets import ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Group
from .serializers import GroupSerializer
from .permissions import IsAuthenticatedReadOnly

class GroupViewSet(ReadOnlyModelViewSet):
    """
    Group API - faqat GET, faqat login foydalanuvchilar.
    Foydalanuvchi faqat o'ziga tegishli guruhlarni ko'radi.
    Admin panelda to'liq CRUD ishlaydi.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['course', 'is_active']

    def get_queryset(self):
        user = self.request.user

        # Superadmin va sifatchi → hamma guruhlarni ko'radi
        if user.is_superuser or hasattr(user, 'sifatchi_profile'):
            return Group.objects.all()

        # Katta ustoz → faqat o'z guruhlari
        if hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            return Group.objects.filter(main_teacher=high_teacher)

        # Yordamchi ustoz → faqat o'z guruhlari
        if hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            return Group.objects.filter(assistant_teacher=assistant)

        # Talaba → faqat o'z guruhi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return Group.objects.filter(id=student.group.id)

        # Boshqalar → hech narsa ko'rmaydi
        return Group.objects.none()

# -------------------- NEW GROUP ----------------------------------

# -----------------------------------------------------------------------




# -------------------- TASK VIEWS NEW VERSION -----------------------------
from rest_framework import viewsets,  filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import SAFE_METHODS

from .models import Task, KnescopeVideoUrl
from student.models import Student
from .serializers import TaskSerializer
from .permissions import  CanReviewTask



# YANGI VAZIFALAR YARATISH UCHUN
class TaskViewSet(viewsets.ModelViewSet):
    """Vazifalar"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'kinescope_video']
    ordering_fields = ['created_at', 'updated_at']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]
        elif self.action == 'create':
            return [IsAuthenticated(), IsStudent()]
        elif self.action in ['partial_update', 'update', 'review']:
            return [IsAuthenticated(), CanReviewTask()]
        return [IsAuthenticated()]

    def get_serializer_class(self):

        return TaskSerializer

    def get_queryset(self):
        user = self.request.user

        # 🔹 Superadmin va staff barcha tasklarni ko'radi
        if user.is_superuser or user.is_staff:
            return Task.objects.all()

        # Sifatchi hamma vazifalarni ko'ra oladi
        if hasattr(user, 'sifatchi_profile'):
            return Task.objects.all()

        # Katta ustoz o'z guruhlari vazifalarini ko'ra oladi
        if hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            groups = Group.objects.filter(main_teacher=high_teacher)
            students = Student.objects.filter(group__in=groups)
            return Task.objects.filter(student__in=students)

        # Yordamchi ustoz o'z guruhlari vazifalarini ko'ra oladi
        if hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            groups = Group.objects.filter(assistant_teacher=assistant)
            students = Student.objects.filter(group__in=groups)
            return Task.objects.filter(student__in=students)

        # Talaba faqat o'z vazifalarini ko'ra oladi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            return Task.objects.filter(student=student)

        return Task.objects.none()

    def perform_create(self, serializer):
        """Talaba vazifa yuklaganda avtomatik student qo'shiladi"""
        if not hasattr(self.request.user, 'student_profile'):
            raise PermissionDenied("Faqat talaba vazifa yuklay oladi")

        serializer.save(
            student=self.request.user.student_profile
        )


    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def group_tasks(self, request):
        """
        Assistant teacher va Superadmin uchun guruh tasklari
        """
        user = request.user

        # 🔹 Superadmin → barcha tasklar
        if user.is_superuser:
            tasks = Task.objects.all()

        # 🔹 Assistant teacher → o‘z guruhlari tasklari
        elif hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            groups = Group.objects.filter(assistant_teacher=assistant)
            students = Student.objects.filter(group__in=groups)
            tasks = Task.objects.filter(student__in=students)

        # 🔹 Boshqalar → ruxsat yo‘q
        else:
            raise PermissionDenied("Sizda bu sahifani ko‘rish huquqi yo‘q")

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

# ----------------------------------------------------------------------------
# ---------------  TEACHER COMMENT VIEWS



# --------------------- STUDENT SPECIFIC VIEWS ---------------------
from rest_framework import generics
from rest_framework.views import APIView

#----------------------  NEW STUDENT VIDEO KODI ------------------------

class StudentVideoListView(generics.ListAPIView):
    """Talaba va superadmin uchun videolar ro'yxati"""
    serializer_class = KnescopeVideoUrlSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superadmin barcha videolarni ko'radi
        if user.is_superuser:
            return KnescopeVideoUrl.objects.all()

        # Agar foydalanuvchi talaba bo'lsa
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return KnescopeVideoUrl.objects.filter(group=student.group)

        # Boshqalar hech narsani ko'ra olmaydi
        return KnescopeVideoUrl.objects.none()



# ------------------------  NEW NOTION ----------------------

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import NotionURL
from .serializers import NotionURLSerializer

class NotionURLViewSet(viewsets.ModelViewSet):
    queryset = NotionURL.objects.all()
    serializer_class = NotionURLSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superadmin → barcha Notion URL
        if user.is_superuser:
            return NotionURL.objects.all()

        # High Teacher → faqat o'z Notion URL'lari
        if hasattr(user, 'high_teacher_profile'):
            return NotionURL.objects.filter(main_teacher=user.high_teacher_profile)

        # Boshqalar → faqat o'qish mumkin
        return NotionURL.objects.all()  # GET ishlaydi, POST/PUT/DELETE rad qilinadi

    # CREATE
    def perform_create(self, serializer):
        user = self.request.user

        if user.is_superuser:
            serializer.save()
        elif hasattr(user, 'high_teacher_profile'):
            serializer.save(main_teacher=user.high_teacher_profile)
        else:
            raise PermissionDenied("Sizga Notion qo'shish huquqi berilmagan")

    # UPDATE
    def perform_update(self, serializer):
        user = self.request.user
        instance = self.get_object()

        if user.is_superuser:
            serializer.save()
        elif hasattr(user, 'high_teacher_profile') and instance.main_teacher == user.high_teacher_profile:
            serializer.save()
        else:
            raise PermissionDenied("Sizga Notion tahrirlash huquqi berilmagan")

    # DELETE
    def perform_destroy(self, instance):
        user = self.request.user

        if user.is_superuser:
            instance.delete()
        elif hasattr(user, 'high_teacher_profile') and instance.main_teacher == user.high_teacher_profile:
            instance.delete()
        else:
            raise PermissionDenied("Sizga Notion o'chirish huquqi berilmagan")

# --------------------------------------------------------------------

#  COMENT YOZISHI UCHUN


# from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated
# from .models import TeacherComment
# from .serializers import TeacherCommentSerializer
# from .permissions import IsAssistantTeacherOrAdmin, IsOwnerOrReadOnly
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import TeacherComment
from .serializers import TeacherCommentSerializer
from .permissions import IsAssistantTeacherOrAdmin, IsOwnerOrReadOnly


class TeacherCommentViewSet(viewsets.ModelViewSet):
    queryset = TeacherComment.objects.all()
    serializer_class = TeacherCommentSerializer
    permission_classes = [IsAuthenticated, IsAssistantTeacherOrAdmin, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        """SUPERADMIN va ASSISTANT_TEACHER comment yozishi mumkin"""
        user = self.request.user

        if hasattr(user, 'assistant_teacher_profile'):
            serializer.save(assistant_teacher=user.assistant_teacher_profile)
        elif user.is_superuser:
            # ✅ SUPERADMIN comment yozishi mumkin
            serializer.save()
        else:
            raise PermissionDenied("Faqat admin va yordamchi ustoz comment yozishi mumkin")

    def get_queryset(self):
        user = self.request.user

        # SUPERADMIN → hamma commentlarni ko'radi
        if user.is_superuser:
            return TeacherComment.objects.all()

        # ASSISTANT_TEACHER → hamma commentlarni ko'radi
        if hasattr(user, 'assistant_teacher_profile'):
            return TeacherComment.objects.all()

        # TALABA → faqat o'z vazifasidagi commentlarni ko'radi
        if hasattr(user, 'student_profile'):
            return TeacherComment.objects.filter(task__student=user.student_profile)

        return TeacherComment.objects.none()




#----------------------------- KNESCOPE URL VIEWS NEW ------------------------------
from rest_framework.viewsets import ReadOnlyModelViewSet
from .permissions import IsSuperAdminOrSifatchiReadOnly

class KnescopeVideoUrlViewSet(ReadOnlyModelViewSet):
    """Kinescope videolari - faqat GET, faqat superadmin va sifatchi"""
    queryset = KnescopeVideoUrl.objects.all()
    serializer_class = KnescopeVideoUrlSerializer
    permission_classes = [IsSuperAdminOrSifatchiReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title']
    filterset_fields = ['course', 'group']


#


#-----------------------------  sifatchi/views.py ---------------------------------------------

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import SifatchiProfile
from .serializers import SifatchiProfileSerializer

class SifatchiProfileViewSet(ReadOnlyModelViewSet):
    """
    Sifatchi Profile API:

    - Sifatchi:
        * GET → faqat o‘z profilini ko‘radi
        * PATCH → faqat o‘z profilidagi ruxsat berilgan maydonlarni tahrirlashi mumkin
        * POST / DELETE → umuman yo‘q (API da ko‘rinmaydi)

    - Superadmin:
        * GET → barcha Sifatchi profillarini ko‘radi
        * PATCH → barcha Sifatchi profillarini tahrirlashi mumkin
    """
    serializer_class = SifatchiProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Superadmin → barcha profillar
        if user.is_superuser:
            return SifatchiProfile.objects.all()

        # Sifatchi → faqat o‘z profilini ko‘radi
        if hasattr(user, 'sifatchi_profile'):
            return SifatchiProfile.objects.filter(user=user)

        # Boshqalar → hech narsa ko‘rmaydi
        return SifatchiProfile.objects.none()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # Ruxsat berilgan maydonlar
        allowed_fields = ['full_name', 'image', 'department', 'phone', 'email', 'is_active']

        # Superadmin → barcha profillarni tahrirlashi mumkin
        if user.is_superuser:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # Sifatchi → faqat o‘z profilini tahrirlashi mumkin
        if hasattr(user, 'sifatchi_profile') and instance.user == user:
            for field in allowed_fields:
                if field in request.data:
                    setattr(instance, field, request.data[field])
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        return Response(
            {"detail": "You do not have permission to edit this profile."},
            status=403
        )

