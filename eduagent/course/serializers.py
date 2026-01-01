from rest_framework import serializers

from .models import Course, High_Teacher, Assistant_Teacher, Group
from .models import SifatchiProfile
from django.contrib.auth import get_user_model

User = get_user_model()


# ----------------------------- Course Serializer -----------------------------
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# --------------------------- High Teacher Serializer -------------------------
from rest_framework import serializers
from .models import High_Teacher

class HighTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = High_Teacher
        fields = [
            'id', 'full_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'job', 'experience_year',
            'info_knowladge', 'image', 'user'
        ]
        read_only_fields = ['id', 'phone_number', 'user']  # faqat yuqoridagi maydonlar tahrirlansa bo‘ladi


# ----------------------- Assistant Teacher Serializer -----------------------
class AssistantTeacherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Assistant_Teacher
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'job', 'experience_year',
            'info_knowladge', 'image'
        ]
        read_only_fields = ['id','user','phone_number','gender']

    def update(self, instance, validated_data):
        """
        SuperAdmin va Assistant Teacher uchun alohida update logikasi
        """
        request = self.context.get('request')

        # Agar SuperAdmin bo'lsa, barcha maydonlarni tahrirlashga ruxsat
        if request and request.user.is_superuser:
            return super().update(instance, validated_data)

        # Assistant Teacher uchun faqat ruxsat etilgan maydonlar
        allowed_fields = [
            'full_name', 'date_of_birth', 'email',
            'job', 'experience_year', 'info_knowladge', 'image'
        ]

        # Faqat ruxsat etilgan maydonlarni yangilash
        for attr, value in validated_data.items():
            if attr in allowed_fields:
                setattr(instance, attr, value)

        instance.save()
        return instance



# ----------------------- Sifatchi  Serializer -----------------------
class SifatchiProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = SifatchiProfile
        fields = [
            'id', 'user', 'full_name', 'image', 'employee_id',
            'department', 'phone', 'email', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



# ---------------------------  GROUP SERIALIZERS --------------------------------------
from rest_framework import serializers
from .models import Group
from .serializers import CourseSerializer
from .serializers import HighTeacherSerializer, AssistantTeacherSerializer
from student.serializers import StudentProfileSerializer

class GroupSerializer(serializers.ModelSerializer):
    main_teacher = HighTeacherSerializer(read_only=True)
    main_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=High_Teacher.objects.all(), write_only=True, required=False, allow_null=True
    )

    assistant_teacher = AssistantTeacherSerializer(many=True, read_only=True)
    assistant_teacher_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Assistant_Teacher.objects.all(), write_only=True, required=False
    )

    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(), write_only=True
    )

    # Talabalar nested
    students = StudentProfileSerializer(source='group_students', many=True, read_only=True)

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'course', 'course_id',
            'main_teacher', 'main_teacher_id',
            'assistant_teacher', 'assistant_teacher_ids',
            'students', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# -------------------------------------------------------------------------------------




# -------------------------------  TASK SERIALIZERS -------------------------------------
from .models import Task
from student.models import Student

# Task Serializer VAZIFA UCHUN IDEAL VAZIFA SERIALIZERS

class TaskSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    kinescope_title = serializers.CharField(source='kinescope_video.title',read_only=True)

    assistant_teacher_name = serializers.CharField(
        source='assistant_teacher.full_name',
        read_only=True,
        allow_null=True
    )
    average_score = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()

    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        write_only=True,
        required=False
    )

    assistant_teacher = serializers.PrimaryKeyRelatedField(
        queryset=Assistant_Teacher.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            'id', 'kinescope_video', 'kinescope_title',
            'student', 'student_name',
            'assistant_teacher', 'assistant_teacher_name',
            'submitted_file', 'title', 'status',
            'average_score','total_comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id','created_at', 'updated_at', 'average_score', 'total_comments']

    def get_average_score(self, obj):
        """Vazifaning o'rtacha bahosini hisoblash"""
        comments = obj.teacher_comments.filter(score__isnull=False)
        if comments.exists():
            total = sum(comment.score for comment in comments)
            return round(total / comments.count(), 2)
        return None

    def get_total_comments(self, obj):
        """Vazifaga yozilgan kommentlar soni"""
        return obj.teacher_comments.count()






# ------------------------------ NOTION UCHUN SERIALIZERS ------------------------------
from rest_framework import serializers
from .models import NotionURL, High_Teacher
from django.contrib.auth import get_user_model

User = get_user_model()  # CustomUser bilan ishlash

class NotionURLSerializer(serializers.ModelSerializer):
    # Read-only maydon (faqat GET)
    main_teacher = serializers.PrimaryKeyRelatedField(read_only=True)

    # Write-only maydon (POST va PUT/PATCH uchun)
    main_teacher_id = serializers.PrimaryKeyRelatedField(
        queryset=High_Teacher.objects.all(),
        write_only=True,
        source='main_teacher',
        required=False,
        allow_null=True
    )

    class Meta:
        model = NotionURL
        fields = [
            'id',
            'title',
            'notion_url',
            'main_teacher_id',
            'main_teacher',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

# -------------------------------  TEACHER COMMENT SERIALIZERS ----------------------------------

# Teacher commnet yozish serializer
from rest_framework import serializers
from .models import TeacherComment


class TeacherCommentSerializer(serializers.ModelSerializer):
    # shunda coment hamda baho uchun

    assistant_teacher_name = serializers.CharField(
        source='assistant_teacher.full_name',
        read_only=True
    )
    student_name = serializers.CharField(
        source='task.student.full_name',
        read_only=True
    )
    task_title = serializers.CharField(
        source='task.kinescope_video.title',
        read_only=True
    )

    # Score display uchun
    score_display = serializers.CharField(
        source='get_score_display',
        read_only=True
    )

    # Task bilan bog'lanish uchun
    task = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        write_only=True
    )

    class Meta:
        model = TeacherComment
        fields = [
            'id',
            'task',  # task ID bilan bog'lanadi
            'task_title',  # taskning video lesson sarlavhasi
            'student_name',  # student ismi
            'assistant_teacher',  # assistant teacher ID
            'assistant_teacher_name',  # assistant teacher ismi
            'comment',
            'score',
            'score_display',
            'created_at'

        ]
        read_only_fields = ['id','assistant_teacher_name', 'student_name', 'task_title', 'score_display', 'created_at']




# kinescope link videos

from rest_framework import serializers
from .models import KnescopeVideoUrl

class KnescopeVideoUrlSerializer(serializers.ModelSerializer):
    # O'qish uchun (faqat frontend uchun)
    course_name = serializers.CharField(source='course.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    # ✅ Yozish uchun (asosiy - ID qabul qiladi)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        write_only=True,
        source='course',
        required=False,
        allow_null=True
    )

    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        write_only=True,
        source='group',
        required=False,
        allow_null=True
    )


    class Meta:
        model = KnescopeVideoUrl
        fields = [
            'id',
            'title',
            'kinescope_video_link',
            'course_id','course_name',
            'group_id','group_name',
            'created_at',
        ]
        read_only_fields = ['id','created_at']


