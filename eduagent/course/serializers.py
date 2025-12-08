from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from authentication.models import SifatchiProfile
from .models import Course, High_Teacher, Assistant_Teacher, Group, VideoLesson
from authentication.models import SifatchiProfile
from django.contrib.auth import get_user_model

User = get_user_model()


# ----------------------------- Course Serializer -----------------------------
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# --------------------------- High Teacher Serializer -------------------------
class HighTeacherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = High_Teacher
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'job', 'experience_year',
            'info_knowladge', 'image', 'notion_url'
        ]
        read_only_fields = ['id']


# ----------------------- Assistant Teacher Serializer -----------------------
class AssistantTeacherSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Assistant_Teacher
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'job', 'experience_year',
            'info_knowladge', 'image'
        ]
        read_only_fields = ['id']




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






# ------------------------------- Group Serializer ----------------------------
class GroupSerializer(serializers.ModelSerializer):
    # Nested representation uchun
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

    # studentlar ham korinadi endi
    students = SifatchiProfileSerializer(source='group_students', many=True, read_only=True)

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'course', 'course_id',
            'main_teacher', 'main_teacher_id',
            'assistant_teacher', 'assistant_teacher_ids', 'students',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        main_teacher = validated_data.pop('main_teacher_id', None)
        assistant_teachers = validated_data.pop('assistant_teacher_ids', [])
        course = validated_data.pop('course_id')

        group = Group.objects.create(course=course, main_teacher=main_teacher, **validated_data)
        if assistant_teachers:
            group.assistant_teacher.set(assistant_teachers)
        return group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.is_active = validated_data.get('is_active', instance.is_active)

        main_teacher = validated_data.get('main_teacher_id', instance.main_teacher)
        instance.main_teacher = main_teacher

        course = validated_data.get('course_id', instance.course)
        instance.course = course

        assistant_teachers = validated_data.get('assistant_teacher_ids', None)
        if assistant_teachers is not None:
            instance.assistant_teacher.set(assistant_teachers)

        instance.save()
        return instance


# --------------------------- Video Lesson Serializer -------------------------
class VideoLessonSerializer(serializers.ModelSerializer):
    course = CourseSerializer(many=True, read_only=True)
    course_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all(), write_only=True
    )

    group = GroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), write_only=True, required=False
    )

    uploaded_by = serializers.PrimaryKeyRelatedField(
        queryset=SifatchiProfile.objects.all()
    )

    class Meta:
        model = VideoLesson
        fields = [
            'id', 'title', 'description', 'video_file',
            'course', 'course_ids',
            'group', 'group_ids',
            'duration', 'file_size', 'uploaded_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'file_size', 'created_at', 'updated_at']


# =============================================================
# bunga ozgartisih kiritildi
    def create(self, validated_data):
        course_ids = validated_data.pop('course_ids', [])
        #======================================================
        # 🧩 MUHIM YECHIM
        if not isinstance(course_ids, list):
            raise ValidationError("course_ids list bo‘lishi kerak")
        #======================================================

        group_ids = validated_data.pop('group_ids', [])
        video = VideoLesson.objects.create(**validated_data)

        if course_ids:
            video.course.set(course_ids)
        if group_ids:
            video.group.set(group_ids)
        return video

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.video_file = validated_data.get('video_file', instance.video_file)
        instance.duration = validated_data.get('duration', instance.duration)
        instance.uploaded_by = validated_data.get('uploaded_by', instance.uploaded_by)

        course_ids = validated_data.get('course_ids', None)
        if course_ids is not None:
            instance.course.set(course_ids)

        group_ids = validated_data.get('group_ids', None)
        if group_ids is not None:
            instance.group.set(group_ids)

        instance.save()
        return instance

from .models import Task
from student.models import Student
# Task Serializer
class TaskSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    video_title = serializers.CharField(source='video_lesson.title', read_only=True)
    assistant_teacher_name = serializers.CharField(
        source='assistant_teacher.full_name',
        read_only=True,
        allow_null=True
    )

    student = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        write_only=True
    )
    video_lesson = serializers.PrimaryKeyRelatedField(
        queryset=VideoLesson.objects.all(),
        write_only=True
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
            'id', 'video_lesson', 'video_title',
            'student', 'student_name',
            'assistant_teacher', 'assistant_teacher_name',
            'submitted_file', 'comment', 'score',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id','created_at', 'updated_at']


# Task Review uchun alohida serializer
class TaskReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['score', 'comment']
