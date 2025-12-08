from tokenize import group

# ============================================================================
#  SHUNDA SHU YANGI KODMI
# =============================================================================


from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import Student
from .serializers import StudentProfileSerializer
from .permissions import IsStudent
from course.models import VideoLesson, Task
from course.serializers import VideoLessonSerializer, TaskSerializer


# --------------------- STUDENT PROFILE ---------------------
class StudentProfileViewSet(viewsets.ModelViewSet):
    """Student o'z profilini ko'rish"""
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        user = self.request.user
        if hasattr(self.request.user, 'student_profile'):
            return Student.objects.filter(id=self.request.user.student_profile.id)

        # staff ham student profilini student kabi koradi
        if user.role in ["staff", "superadmin"]:
            return Student.objects.all()

        return Student.objects.none()

    def create(self, request, *args, **kwargs):
        # Yangi profil yaratish taqiqlangan
        return Response({"detail": "Creation not allowed."}, status=403)

    def destroy(self, request, *args, **kwargs):
        # Profilni o'chirish taqiqlangan
        return Response({"detail": "Deletion not allowed."}, status=403)


    @action(detail=False, methods=['get'])
    def me(self, request):
        """Studentning o'z profili"""
        if hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
            serializer = self.get_serializer(student)
            return Response(serializer.data)
        return Response(
            {"detail": "Student profile topilmadi."},
            status=status.HTTP_404_NOT_FOUND
        )


# --------------------- STUDENT VIDEOS ---------------------
class StudentVideoListView(generics.ListAPIView):
    """Student uchun videolar ro'yxati"""
    serializer_class = VideoLessonSerializer
    permission_classes = [IsAuthenticated], # IsStudent
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']

    def get_queryset(self):
        user = self.request.user


        #Swagger UI uchun tekshiriuv
        if getattr(self,"swagger_fake_view", False) or not self.request.user.is_authenticated:
            return VideoLesson.objects.none()


        # Agar student bolsa
        if hasattr(user, 'student_profile'):
            student = user.student_profile
            if student.group:
                return VideoLesson.objects.filter(group=student.group)
            return VideoLesson.objects.none()  # studentda group bo‘lmasa

        # Agar staff / teacher / head_teacher bo‘lsa
        if user.role in ['staff', 'teacher', 'head_teacher']:
            return VideoLesson.objects.all()  # barcha student videolari

        # Boshqa user bo‘lsa
        return VideoLesson.objects.none()

class StudentVideoDetailView(generics.RetrieveAPIView):
    """Student uchun video batafsil"""
    serializer_class = VideoLessonSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'video_id'

    def get_queryset(self):
        user = self.request.user

        if hasattr(user, 'student_profile') and user.student_profile.group:
            student = user.student_profile
            return VideoLesson.objects.filter(group=student.group)

        if user.role in ['staff', 'superadmin', 'teacher', 'head_teacher']:
            return VideoLesson.objects.all()


# --------------------- STUDENT TASKS ---------------------
class StudentTaskViewSet(viewsets.ModelViewSet):
    """Student vazifalari - FAQAT CREATE va READ"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['video_lesson']
    ordering_fields = ['created_at', 'updated_at', 'score']

    def get_queryset(self):
        # Student faqat o'z vazifalarini ko'ra oladi
        student = self.request.user.student_profile
        return Task.objects.filter(student=student)

    def perform_create(self, serializer):
        # Student vazifa yaratganda o'zi avtomatik qo'shiladi
        student = self.request.user.student_profile
        serializer.save(student=student, status='yuklandi')

    # Student faqat vazifa yuklay oladi, update/delete qila olmaydi
    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Student vazifani yangilay olmaydi."},
            status=status.HTTP_403_FORBIDDEN
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Student vazifani o'chira olmaydi."},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Yuklangan lekin tekshirilmagan vazifalar"""
        student = request.user.student_profile
        tasks = Task.objects.filter(student=student, status='yuklandi')

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reviewed(self, request):
        """Tekshirilgan vazifalar"""
        student = request.user.student_profile
        tasks = Task.objects.filter(student=student, status='tekshirildi')

        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


# --------------------- SUBMIT TASK ---------------------
class SubmitTaskView(APIView):
    """Student video uchun vazifa yuklash"""
    permission_classes = [IsAuthenticated, IsStudent]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, video_id=None):
        """Student barcha vazifalarini ko'radi"""
        student = request.user.student_profile
        tasks = Task.objects.filter(student=student)

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request, video_id):
        try:
            video = VideoLesson.objects.get(id=video_id)
            student = request.user.student_profile

            # Student o'z guruhidagi videoga vazifa yuklay oladi
            if student.group and not video.group.filter(id=student.group.id).exists():
                return Response(
                    {"detail": "Bu video sizning guruhingizga tegishli emas."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Vazifa allaqachon yuklanganmi?
            existing_task = Task.objects.filter(
                video_lesson=video,
                student=student
            ).first()

            if existing_task:
                # Agar vazifa bor bo'lsa, yangilash mumkin
                serializer = TaskSerializer(existing_task, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Yangi vazifa yaratish
            serializer = TaskSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                task = serializer.save(
                    video_lesson=video,
                    student=student,
                    status='yuklandi'
                )
                return Response(
                    TaskSerializer(task).data,
                    status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except VideoLesson.DoesNotExist:
            return Response(
                {"detail": "Video topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )


# --------------------- DASHBOARD ---------------------
class StudentDashboardView(APIView):
    """Student dashboard"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if hasattr(user,'student_profile'):
            student = user.student_profile
            tasks = Task.objects.filter(student=student)
            recent_videos = VideoLesson.objects.filter(group=student.group).order_by('-created_at')[:5] if student.group else []


        # Agar staff, superadmin yoki teacher bo'lsa
        elif user.role in ['staff', 'superadmin', 'teacher', 'head_teacher']:
            student = None  # staff uchun student info yo‘q
            tasks = Task.objects.all()  # barcha student vazifalari
            recent_videos = VideoLesson.objects.all().order_by('-created_at')[:5]

        # Boshqa foydalanuvchi bo'lsa
        else:
            student = None
            tasks = Task.objects.none()
            recent_videos = []


        # Statistikalar
        total_tasks = Task.objects.filter(student=student).count()
        reviewed_tasks = Task.objects.filter(student=student, status='tekshirildi').count()
        pending_tasks = Task.objects.filter(student=student, status='yuklandi').count()

        # O'rtacha baho
        graded_tasks = Task.objects.filter(student=student, score__isnull=False)
        average_score = None
        if graded_tasks.exists():
            average_score = sum(task.score for task in graded_tasks) / graded_tasks.count()

        # Oxirgi videolar
        recent_videos = []
        if student.group:
            recent_videos = VideoLesson.objects.filter(
                group=student.group
            ).order_by('-created_at')[:5]

        data = {
            'student': {
                'full_name': student.full_name if student else None,
                'group': student.group.name if student.group else None,
                'course': student.group.course.name if student.group and student.group.course else None,
            },
            'statistics': {
                'total_tasks': total_tasks,
                'reviewed_tasks': reviewed_tasks,
                'pending_tasks': pending_tasks,
                'average_score': average_score,
            },
            'recent_videos': VideoLessonSerializer(recent_videos, many=True).data,
        }

        return Response(data)


# --------------------- GROUP INFO ---------------------
class StudentGroupInfoView(APIView):
    """Student guruh ma'lumotlari"""
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        student = request.user.student_profile

        if not student.group:
            return Response(
                {"detail": "Siz hali guruhga qo'shilmagansiz."},
                status=status.HTTP_404_NOT_FOUND
            )

        group = student.group

        data = {
            'group': {
                'name': group.name,
                'course': group.course.name if group.course else None,
                'main_teacher': group.main_teacher.full_name if group.main_teacher else None,
                'assistant_teachers': [
                    teacher.full_name for teacher in group.assistant_teacher.all()
                ],
            },
            'classmates': [
                {
                    'id': classmate.id,
                    'full_name': classmate.full_name,
                }
                for classmate in Student.objects.filter(group=group).exclude(id=student.id)
            ]
        }

        return Response(data)


