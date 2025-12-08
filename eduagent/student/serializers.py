#-------------------------------------------------------------------
# BU TOLIQ STUDENT SERIALIZER BUNDA YOZILGAN BUNDA
#RO'YXAT, KORINISH, YARATISH, STUDENT PROFILI UCHUN SERIALIZER
#
#
#===========================================================================
from django.contrib.auth import get_user_model
from django.template.context_processors import request
from django.template.defaulttags import comment
from rest_framework import serializers
from rest_framework.exceptions import server_error

# from authentication.bot import phone_handler
from .models  import High_Teacher
from .models import Student, ChatMessage, StudentHistory
import os

from student.models import Student
from course.models import High_Teacher

User = get_user_model()



#===================================================
# STUDENT HISTORY SERIALIZER
#===================================================
class StudentHistorySerializer(serializers.ModelSerializer):
    """Talaba tarixi operator tomonidan yoziladi unga coment u tolov qildi qilmadi hklar uchun"""
    """StringRelatedField ---> bu masalan id 1 yokida 2 deb user id isi chiqadi shunda shu id orniga "ism" korinishida chiqishi uchun "StringRelatedField" shu kerak bo'ladi"""
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = StudentHistory
        fields = ["id", "author", "comment", "created_at"]
        ref_name = "StudentHistorySerializer"


#======================================================
# Shunda bu Talabalar RO'YXATI SERIALIZER
#=======================================================

class StudentListSerializer(serializers.ModelSerializer):
    """Studentlar ro'yxati uchun serializer"""
    image_url = serializers.SerializerMethodField()  # imageni toliq url manzilda berish

    class Meta:
        model = Student
        fields = ["id", "full_name", "image", "image_url", "gender", "phone_number", "email", "created_at"]
        ref_name = "StudentListSerializer"

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)  # absulute ning vazifasi ---> bu to'liq URL yasaydi
            return obj.image.url
        return None


# ==============================================================================
# STUDENT HAQIDA TO'LIQ YIG'ILGAN MA'LUMOTLAR - SIFATCHI UCHUN STUDENT HAQIDA TOLIQ MALUMOT)
# ==============================================================================

class StudentDetailSerializer(serializers.ModelSerializer):
    """Student haqida to'liq ma'lumotlar jamlanmasi """
    history =  serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    average_score = serializers.ReadOnlyField()


    class Meta:
        model = Student
        fields = [
            "id", "full_name", "date_of_birth", "gender", "phone_number", "email", "image","image_url", "created_at", "updated_at","history", ""
        ]
        ref_name = "StudentDetailSerializer"

    def get_image_url(self, obj):
        if obj.image:
            try:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
            except:
                return None
        return None

    def get_history(self, obj):
        try:
            history_items = StudentHistory.objects.filter(student=obj).select_related('author').order_by('-created_at')[:20]
            return StudentHistorySerializer(history_items, many=True).data
        except:
            return []


#================================================================
#   Student create/update serializer kodi student yaratosh tahrir va delete uchun
#================================================================

class StudentCreateUpdateSerializer(serializers.ModelSerializer):
    """
      Admin yangi student yaratishi uchun serializer.
      Shu serializer yordamida:
      1️⃣ Student profili yaratiladi
      2️⃣ Shu studentga tegishli CustomUser (phone_number va password) yaratiladi
      """

    # ---------------------------
    # LOGIN MAYDONLARI (NEW)
    # ---------------------------

    phone_number = serializers.CharField(write_only=True, required=True, help_text="Foydalanuvchi login phone_number")
    password = serializers.CharField(write_only=True, required=True, help_text="Foydalanuvchi password")





    """Student yaratish va tahrirlash xolos delete yoq"""
    image = serializers.ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    assigned_course = serializers.SerializerMethodField(read_only=True)
    assigned_course_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    assigned_group = serializers.SerializerMethodField(read_only=True)
    assigned_group_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    assigned_teacher = serializers.SerializerMethodField(read_only=True)
    assigned_teacher_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    assigned_assistant_teacher = serializers.SerializerMethodField(read_only=True)
    assigned_assistant_teacher_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Student
        fields = [
            "id", "full_name", "date_of_birth", "gender", "phone_number", "password", "email",
            "image", "image_url",
            "assigned_course_id", "assigned_course",
            "assigned_group_id", "assigned_group",
            "assigned_teacher_id", "assigned_teacher",
            "assigned_assistant_teacher_id", "assigned_assistant_teacher",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "image_url",
                            "assigned_course", "assigned_group",
                            "assigned_teacher", "assigned_assistant_teacher"]

        ref_name = "StudentCreateUpdateSerializer"

    def create(self, validated_data):
        """ Yangi student yaratish"""

        phone_number = validated_data.pop('phone_nummber')
        password = validated_data.pop('password')

        course_id = validated_data.pop('assigned_course_id', None)
        group_id = validated_data.pop('assigned_group_id', None)
        teacher_id = validated_data.pop('assigned_teacher_id', None)
        assistant_id = validated_data.pop('assigned_assistant_teacher_id', None)



        # ---------------------------
        # 1️⃣ CustomUser yaratish
        # ---------------------------
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            role='student'  # role = student qilib beramiz
        )

        # ---------------------------
        # 2️⃣ Student yaratish
        # ---------------------------
        student = Student.objects.create(
            user=user,
            created_by = self.context['request'].user,
            **validated_data
        )



        # Foreignkeylarni bog'lash
        if course_id:
            student.assigned_course_id = course_id
        if group_id:
            student.assigned_group_id = group_id
        if teacher_id:
            student.assigned_teacher_id = teacher_id
        if assistant_id:
            student.assigned_assistant_teacher_id = assistant_id

        student.save()

        # ---------------------------
        # 4️⃣ StudentHistory yozish
        # ---------------------------

        StudentHistory.objects.create(
            student=student,
            author=self.context['request'].user,
            comment="✅ Yangi student yaratildi"
        )
        return student




    # =======================
    # SerializerMethodField lar
    # =======================
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_assigned_course(self, obj):
        if obj.assigned_course:
            return {"id": obj.assigned_course.id, "name": obj.assigned_course.name}
        return None

    def get_assigned_group(self, obj):
        if obj.assigned_group:
            return {"id": obj.assigned_group.id, "name": obj.assigned_group.name}
        return None

    def get_assigned_teacher(self, obj):
        if obj.assigned_teacher:
            return {"id": obj.assigned_teacher.id, "name": obj.assigned_teacher.name}
        return None

    def get_assigned_assistant_teacher(self, obj):
        if obj.assigned_assistant_teacher:
            return {"id": obj.assigned_assistant_teacher.id, "name": obj.assigned_assistant_teacher.name}
        return None


# ========================================================================================
# Update qilish
# ========================================================================================

    def update(self, instance, validated_data):
        # ---------------------------
        # 1️⃣ Phone va password olish (agar berilgan bo'lsa)
        # ---------------------------

        phone_number = validated_data.pop('phone_number', None)
        password = validated_data.pop('password', None)



        # ---------------------------
        # 2️⃣ ForeignKey ID larini ajratib olish
        # ---------------------------
        course_id = validated_data.pop('assigned_course_id', None)
        group_id = validated_data.pop('assigned_group_id', None)
        teacher_id = validated_data.pop('assigned_teacher_id', None)
        assistant_id = validated_data.pop('assigned_assistant_teacher_id', None)

        # Oddiy maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # ForeignKeylarni yangilash
        if course_id is not None:
            instance.assigned_course_id = course_id

        if group_id is not None:
            instance.assigned_group_id = group_id

        if teacher_id is not None:
            instance.assigned_teacher_id = teacher_id

        if assistant_id is not None:
            instance.assigned_assistant_teacher_id = assistant_id


        # ---------------------------
        # 5️⃣ CustomUser (login) ma'lumotlarini yangilash
        # ---------------------------
        user = instance.user  # Studentga bog'langan CustomUser
        if phone_number:
            user.phone_number = phone_number
        if password:
            user.set_password(password)  # passwordni hash qilib saqlaydi
        user.save()

    # Studentni saqlash
        instance.save()




        # Tarixga yozish
        StudentHistory.objects.create(
            student=instance,
            author=self.context['request'].user,
            comment="♻️ Student ma'lumotlari tahrirlandi"
        )

        return instance



# =======================================================================
# Student Profile Serializer
# =======================================================================

class StudentProfileSerializer(serializers.ModelSerializer):
    """Student Profile"""
    assigned_teacher = serializers.SerializerMethodField()
    assigned_assistant_teacher = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)
    image_url = serializers.SerializerMethodField()
    assigned_course = serializers.SerializerMethodField()
    assigned_group = serializers.SerializerMethodField()



    class Meta:
        model = Student
        fields = [
            "id", "full_name", "date_of_birth", "gender", "phone_number", "email",
            "assigned_teacher", "assigned_assistant_teacher", "assigned_group","image", "image_url", "assigned_course",
            "created_at", "updated_at"
        ]
        ref_name = "StudentProfileSerializer"

    def get_assigned_teacher(self, obj):
        if obj.assigned_teacher:
            return {
                "id": obj.assigned_teacher.id,
                "name": obj.assigned_teacher.name,
                "code": obj.assigned_teacher.code
            }
        return None

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_assigned_course(self, obj):
        if obj.assigned_course:
            return {"id": obj.assigned_course.id, "name": obj.assigned_course.name}
        return None

    def get_assigned_group(self, obj):
        if obj.assigned_group:
            return {"id": obj.assigned_group.id, "name": obj.assigned_group.name}
        return None

    def get_assigned_assistant_teacher(self, obj):
        if obj.assigned_assistant_teacher:
            return {
                "id": obj.assigned_assistant_teacher.id,
                "name": obj.assigned_assistant_teacher.name
            }
        return None


# ===============================================================
# CHAT MESSAGE SERIALIZER
# ===============================================================
class ChatMessageSerializer(serializers.ModelSerializer):
    """Chat xabarlari"""
    sender = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "message", "file", "file_url", "timestamp"]
        read_only_fields = ["id", "timestamp", "sender", "file_url"]
        ref_name = "TeacherChatMessageSerializer"

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

