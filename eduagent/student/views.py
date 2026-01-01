# ============================================================================
#  SHUNDA SHU YANGI KODMI
# =============================================================================

from rest_framework import   status
from course.models import Task, Group, KnescopeVideoUrl
from course.serializers import  TaskSerializer, KnescopeVideoUrlSerializer

# --------------------- NEW  STUDENT PROFILE ---------------------
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Student
from .serializers import StudentProfileSerializer

class StudentProfileViewSet(viewsets.ModelViewSet):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']  # POST va DELETE yo'q

    def get_queryset(self):
        user = self.request.user

        if user.is_superuser:
            return Student.objects.all()  # superadmin barcha studentlarni ko'radi

        # student faqat o'z profilini ko'radi
        if hasattr(user, 'student_profile'):
            return Student.objects.filter(id=user.student_profile.id)

        # boshqa foydalanuvchi hech narsani ko'ra olmaydi
        return Student.objects.none()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # student faqat o'z profilini edit qilishi mumkin
        if not user.is_superuser and instance != getattr(user, 'student_profile', None):
            raise PermissionDenied("Siz bu profilni tahrirlash huquqiga ega emassiz")

        # faqat ruxsat berilgan maydonlarni yangilash
        allowed_fields = ['date_of_birth', 'gender', 'profiency', 'phone_number', 'email', 'image']
        data = {key: value for key, value in request.data.items() if key in allowed_fields}

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

# -----------------------------------------------------------------------------------


#  -------------------------------- NEW DASHBOARD ---------------------------------
# ----------------------------- DASHBOARD (TO'G'RILANGAN) ---------------------

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from course.models import Task, TeacherComment


class StudentDashboardView(APIView):
    """Student dashboard - TO'G'RILANGAN"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        student = getattr(user, 'student_profile', None)

        recent_videos = []
        total_tasks = reviewed_tasks = pending_tasks = 0
        average_score = None

        if student:
            # Student bo'lsa
            tasks = Task.objects.filter(student=student)
            total_tasks = tasks.count()

            # ✅ TO'G'RILASH: Status bo'yicha hisoblash
            reviewed_tasks = tasks.filter(status='baholandi').count()
            pending_tasks = tasks.filter(status='yuklandi').count()

            # Baholangan vazifalarni olish
            graded_tasks = tasks.filter(status='baholandi')

            if graded_tasks.exists():
                # ✅ TO'G'RILASH: TeacherComment orqali baholarni hisoblash
                task_ids = graded_tasks.values_list('id', flat=True)
                scored_comments = TeacherComment.objects.filter(
                    task_id__in=task_ids,
                    score__isnull=False
                )

                if scored_comments.exists():
                    total_score = sum(comment.score for comment in scored_comments)
                    average_score = total_score / scored_comments.count()

            if student.assigned_group:
                recent_videos = KnescopeVideoUrl.objects.filter(
                    group=student.assigned_group
                ).order_by('-created_at')[:5]

        elif user.role in ['staff', 'superadmin', 'teacher', 'head_teacher']:
            # Admin, staff, teacher uchun
            tasks = Task.objects.all()
            total_tasks = tasks.count()

            # ✅ TO'G'RILASH: Status bo'yicha hisoblash
            reviewed_tasks = tasks.filter(status='baholandi').count()
            pending_tasks = tasks.filter(status='yuklandi').count()

            # Baholangan vazifalar
            graded_tasks = tasks.filter(status='baholandi')

            if graded_tasks.exists():
                # ✅ TO'G'RILASH: Barcha TeacherComment lardan baholarni hisoblash
                scored_comments = TeacherComment.objects.filter(
                    task__in=graded_tasks,
                    score__isnull=False
                )

                if scored_comments.exists():
                    total_score = sum(comment.score for comment in scored_comments)
                    average_score = total_score / scored_comments.count()

            recent_videos = KnescopeVideoUrl.objects.all().order_by('-created_at')[:5]
        else:
            tasks = Task.objects.none()

        data = {
            'student': {
                'full_name': student.full_name if student else None,
                'group': student.assigned_group.name if student and student.assigned_group else None,
                'course': student.assigned_group.course.name if student and student.assigned_group and student.assigned_group.course else None,
            } if student else None,
            'statistics': {
                'total_tasks': total_tasks,
                'reviewed_tasks': reviewed_tasks,
                'pending_tasks': pending_tasks,
                'average_score': round(average_score, 2) if average_score else None,
            },
            'recent_videos': KnescopeVideoUrlSerializer(recent_videos, many=True).data if recent_videos else [],
        }

        return Response(data)
# ---------------------------------------------------------------------------------



# -----------------------------------  STUDENT GROUP INFO VIEW ------------------------------------------

# ------------------------ GROUP INFO (TO'G'RILANGAN) ------------------

class StudentGroupInfoView(APIView):
    """Guruh ma'lumotlari - Student va Admin uchun"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'student':
            try:
                student = user.student_profile
            except AttributeError:
                return Response(
                    {"detail": "Student profili topilmadi."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not student.assigned_group:
                return Response(
                    {"detail": "Siz hali guruhga qo'shilmagansiz."},
                    status=status.HTTP_404_NOT_FOUND
                )

            group = student.assigned_group
            group_id = group.id

        elif user.role in ['staff', 'superadmin', 'teacher', 'head_teacher']:
            group_id = request.query_params.get('group_id')

            if not group_id:
                groups = Group.objects.all()
                data = {
                    'all_groups': [
                        {
                            'id': g.id,
                            'name': g.name,
                            'course': g.course.name if g.course else None,
                            'main_teacher': g.main_teacher.full_name if g.main_teacher else None,
                            'total_students': Student.objects.filter(assigned_group=g).count(),
                        }
                        for g in groups
                    ],
                    'total_groups': groups.count(),
                    'user_role': user.role
                }
                return Response(data)

            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return Response(
                    {"detail": "Guruh topilmadi."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"detail": "Bu sahifaga kirish uchun ruxsat yo'q."},
                status=status.HTTP_403_FORBIDDEN
            )

        students_in_group = Student.objects.filter(assigned_group=group)

        # ✅ TO'G'RILASH: video_lesson emas, kinescope_video orqali
        total_tasks = Task.objects.filter(
            student__assigned_group=group
        ).count()

        data = {
            'group_info': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'course': {
                    'id': group.course.id if group.course else None,
                    'name': group.course.name if group.course else None,
                } if group.course else None,
                'main_teacher': {
                    'id': group.main_teacher.id if group.main_teacher else None,
                    'full_name': group.main_teacher.full_name if group.main_teacher else None,
                    'phone': group.main_teacher.phone if group.main_teacher else None,
                } if group.main_teacher else None,
                'assistant_teachers': [
                    {
                        'id': teacher.id,
                        'full_name': teacher.full_name,
                        'phone': teacher.phone,
                    }
                    for teacher in group.assistant_teacher.all()
                ],
                'created_at': group.created_at,
            },
            'students': [
                {
                    'id': student.id,
                    'full_name': student.full_name,
                    'phone': student.phone,
                    'email': student.email,
                    'joined_at': student.created_at,
                }
                for student in students_in_group
            ],
            'statistics': {
                'total_students': students_in_group.count(),
                'total_videos': KnescopeVideoUrl.objects.filter(group=group).count(),
                'total_tasks': total_tasks,  # ✅ TO'G'RILANDI
            },
            'user_info': {
                'role': user.role,
                'is_viewing_own_group': user.role == 'student' and hasattr(user, 'student_profile') and user.student_profile.assigned_group == group
            }
        }

        return Response(data)
# -------------------------------------------------------------------------------------------------------
