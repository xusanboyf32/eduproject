from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from authentication import permissions
from .models import Course, High_Teacher, Assistant_Teacher, Group, VideoLesson, Task
from .serializers import (
    CourseSerializer, HighTeacherSerializer, AssistantTeacherSerializer,
    GroupSerializer, VideoLessonSerializer, TaskSerializer, TaskReviewSerializer
)
from .permissions import (
    IsSifatchi, IsAssistantTeacher, IsHighTeacher,
    CanUploadVideo, CanReviewTask, IsTaskOwner, IsGroupMember
)
from student.models import Student
from student.permissions import IsStudent


# ---------------------- COURSE VIEWSET ----------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']


    def get_permissions(self):
        # Superuser bo'lsa hamma narsa mumkin
        if self.request.user.is_superuser:
            # return True
            return [AllowAny()]

        # Boshqalar faqat safe methods (GET, HEAD, OPTIONS)
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]

        return [IsAuthenticated()]


    def has_object_permission(self, request, view, obj):
        # Superuser hamma narsaga ruxsat
        if request.user.is_superuser:
            return True

        # Oddiy foydalanuvchi faqat GET/HEAD/OPTIONS va faqat o'z kursini ko'rishi mumkin
        if request.method in permissions.SAFE_METHODS:
            # Masalan, agar siz foydalanuvchi modelida qaysi kursga tegishli ekanini saqlasangiz:
            return obj in request.user.courses.all()  # request.user.courses – ManyToMany yoki ForeignKey

        return False

# -------------------- HIGH TEACHER VIEWSET -------------------
class HighTeacherViewSet(viewsets.ModelViewSet):
    """Katta ustozlar faqat o'qishi mumkin"""
    queryset = High_Teacher.objects.all()
    serializer_class = HighTeacherSerializer
    permission_classes = [IsAuthenticated, IsHighTeacher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email']

    def get_queryset(self):
        # Katta ustoz faqat o'z ma'lumotlarini ko'ra oladi
        if hasattr(self.request.user, 'high_teacher_profile'):
            return High_Teacher.objects.filter(user=self.request.user)
        return High_Teacher.objects.none()


    def create(self, request, *args, **kwargs):
        # Foydalanuvchi orqali create taqiqlanadi
        return Response({"detail": "Creation not allowed."}, status=403)

    def destroy(self, request, *args, **kwargs):
        # Foydalanuvchi tomonidan delete taqiqlanadi
        return Response({"detail": "Deletion not allowed."}, status=403)


# ------------------ ASSISTANT TEACHER VIEWSET -----------------
class AssistantTeacherViewSet(viewsets.ModelViewSet):
    """Yordamchi ustozlar faqat o'qishi mumkin"""
    serializer_class = AssistantTeacherSerializer
    permission_classes = [IsAuthenticated, IsAssistantTeacher]
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'email']

    def get_queryset(self):
        # Yordamchi ustoz faqat o'z ma'lumotlarini ko'ra oladi
        if hasattr(self.request.user, 'assistant_teacher_profile'):
            return Assistant_Teacher.objects.filter(user=self.request.user)
        return Assistant_Teacher.objects.none()



    def create(self, request, *args, **kwargs):
        # Create operatsiyasini foydalanuvchi uchun bloklaymiz
        return Response({"detail": "Creation not allowed."}, status=403)

    def destroy(self, request, *args, **kwargs):
        # Delete operatsiyasini foydalanuvchi uchun bloklaymiz
        return Response({"detail": "Deletion not allowed."}, status=403)


# ----------------------- GROUP VIEWSET -----------------------
class GroupViewSet(viewsets.ModelViewSet):
    """Guruhlarni ko'rish"""
    queryset = Group.objects.filter(is_active=True)
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name']
    filterset_fields = ['course', 'is_active']

    def get_queryset(self):
        user = self.request.user

        # superuser hamma guruhlarni ko'ra oladi
        if user.is_superuser:
            return Group.objects.all()
        # hasatr --> tekshirish bu rostan sifatchimi yokida boshqa bolsa ruxsat agarda u sifatchi bomasa ruxsat yo'q
        # Sifatchi hamma guruhlarni ko'ra oladi
        if hasattr(user, 'sifatchi_profile'):
            return Group.objects.all()

        # Katta ustoz o'z guruhlarini ko'ra oladi
        if hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            return Group.objects.filter(main_teacher=high_teacher)

        # Yordamchi ustoz o'z guruhlarini ko'ra oladi
        if hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            return Group.objects.filter(assistant_teacher=assistant)

        # Talaba o'z guruhini ko'ra oladi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return Group.objects.filter(id=student.group.id)

        return Group.objects.none()

    def get_permissions(self):
        user = self.request.user

        #GET, HEAD , OPTIONS -> barcha authdan o'tganlar -> SAFE_METHODS ga shular kiradi
        if self.request.method in SAFE_METHODS:
            return [IsAuthenticated()]

        # POST, PUT, PATH, DELETE --> faqat superuser qila oladi
        if user.is_superuser:
            return [IsAuthenticated()]

        # Boshqa foydalanuvchilar uchun ruxsat yo'q
        from rest_framework.permissions import BasePermission
        class DenyAll(BasePermission):
            def has_permission(self, request, view):
                return False

        return [DenyAll()]


# -------------------- VIDEO LESSON VIEWSET --------------------
class VideoLessonViewSet(viewsets.ModelViewSet):
    """Video darsliklar"""
    queryset = VideoLesson.objects.all()
    serializer_class = VideoLessonSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    filterset_fields = ['course', 'group']
    ordering_fields = ['created_at', 'title']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            # O'qish uchun barcha autentifikatsiyadan o'tganlar
            return [IsAuthenticated()]
        # Yozish/yaratish uchun faqat sifatchi
        return [IsAuthenticated(), IsSifatchi()]

    def get_queryset(self):
        user = self.request.user
        queryset = VideoLesson.objects.all()

        # Sifatchi hamma videolarni ko'ra oladi
        if hasattr(user, 'sifatchi_profile'):
            return queryset

        # Talaba, ustozlar faqat o'z guruhlari videolarini ko'ra oladi
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return queryset.filter(group=student.group)
            #=========================================================
            return VideoLesson.objects.none()  # studentda group bo'lmas


        elif hasattr(user, 'assistant_teacher_profile'):
            assistant = user.assistant_teacher_profile
            groups = Group.objects.filter(assistant_teacher=assistant)
            return queryset.filter(group__in=groups).distinct()

        elif hasattr(user, 'high_teacher_profile'):
            high_teacher = user.high_teacher_profile
            groups = Group.objects.filter(main_teacher=high_teacher)
            return queryset.filter(group__in=groups).distinct()

        elif user.role in ['staff', 'head_teacher', 'assistant_teacher']:
            return queryset

        return VideoLesson.objects.none()

    def perform_create(self, serializer):
        # Video yuklaganda avtomatik sifatchi profili qo'shiladi
        if hasattr(self.request.user, 'sifatchi_profile'):
            serializer.save(uploaded_by=self.request.user.sifatchi_profile)


# ------------------------ TASK VIEWSET ------------------------
class TaskViewSet(viewsets.ModelViewSet):
    """Vazifalar"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'video_lesson']
    ordering_fields = ['created_at', 'score']

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            # O'qish uchun faqat egasi yoki tekshiruvchi
            return [IsAuthenticated()]
        elif self.action == 'create':
            # Yaratish uchun faqat talaba
            return [IsAuthenticated(), IsStudent()]
        elif self.action in ['partial_update', 'update', 'review']:
            # Yangilash uchun faqat yordamchi ustoz
            return [IsAuthenticated(), CanReviewTask()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'review':
            return TaskReviewSerializer
        return TaskSerializer

    def get_queryset(self):
        user = self.request.user

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
        # Talaba vazifa yuklaganda avtomatik o'zi qo'shiladi
        if hasattr(self.request.user, 'student_profile'):
            student = self.request.user.student_profile
            serializer.save(student=student, status='yuklandi')

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, CanReviewTask])
    def review(self, request, pk=None):
        """Vazifani tekshirish va baholash"""
        task = self.get_object()

        # Faqat o'z guruhidagi talabalarga baho bera oladi
        if hasattr(request.user, 'assistant_teacher_profile'):
            assistant = request.user.assistant_teacher_profile
            # Talaba va yordamchi ustoz bir guruhdami?
            if not task.student.groups.filter(assistant_teacher=assistant).exists():
                return Response(
                    {"detail": "Bu talaba sizning guruhingizda emas."},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(task, data=request.data, partial=True)

        if serializer.is_valid():
            # Baho qo'yilganda status avtomatik o'zgaradi
            updated_task = serializer.save(
                assistant_teacher=request.user.assistant_teacher_profile if hasattr(request.user,
                                                                                    'assistant_teacher_profile') else None,
                status='tekshirildi'
            )
            return Response(TaskSerializer(updated_task).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsStudent])
    def my_tasks(self, request):
        """Talabaning o'z vazifalari"""
        student = request.user.student_profile
        tasks = Task.objects.filter(student=student)

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAssistantTeacher])
    def group_tasks(self, request):
        """Yordamchi ustozning guruh vazifalari"""
        assistant = request.user.assistant_teacher_profile
        groups = Group.objects.filter(assistant_teacher=assistant)
        students = Student.objects.filter(group__in=groups)
        tasks = Task.objects.filter(student__in=students)

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


# --------------------- STUDENT SPECIFIC VIEWS ---------------------
from rest_framework import generics
from rest_framework.views import APIView


class StudentVideoListView(generics.ListAPIView):
    """Talaba uchun videolar ro'yxati"""
    serializer_class = VideoLessonSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        student = self.request.user.student_profile
        if student.group:
            return VideoLesson.objects.filter(group=student.group)
        return VideoLesson.objects.none()


class SubmitTaskView(APIView):
    """Talaba vazifa yuklash"""
    permission_classes = [IsAuthenticated, IsStudent]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, video_lesson_id):
        try:
            video_lesson = VideoLesson.objects.get(id=video_lesson_id)
            student = request.user.student_profile

            # Talaba o'z guruhidagi videoga vazifa yuklay oladi
            if student.group and not video_lesson.group.filter(id=student.group.id).exists():
                return Response(
                    {"detail": "Bu video sizning guruhingizga tegishli emas."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vazifa allaqachon yuklanganmi?
            existing_task = Task.objects.filter(
                video_lesson=video_lesson,
                student=student
            ).first()

            if existing_task:
                return Response(
                    {"detail": "Bu video uchun vazifa allaqachon yuklangan."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = TaskSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(
                    video_lesson=video_lesson,
                    student=student,
                    status='yuklandi'
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except VideoLesson.DoesNotExist:
            return Response(
                {"detail": "Video topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )

