#-------------------------------------------------------------------
# BU TOLIQ STUDENT SERIALIZER BUNDA YOZILGAN BUNDA
#RO'YXAT, KORINISH, YARATISH, STUDENT PROFILI UCHUN SERIALIZER
#
#
#===========================================================================
from django.contrib.auth import get_user_model

User = get_user_model()



# =======================================================================
# Student Profile Serializer NEW VERSION
# =======================================================================

from rest_framework import serializers
from .models import Student

class StudentProfileSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    assigned_course = serializers.SerializerMethodField()
    assigned_group = serializers.SerializerMethodField()
    assigned_teacher = serializers.SerializerMethodField()
    assigned_assistant_teacher = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id", "full_name", "date_of_birth", "gender", "profiency",
            "phone_number", "email", "image", "image_url",
            "assigned_course", "assigned_group", "assigned_teacher", "assigned_assistant_teacher",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "full_name", "created_at", "updated_at", "image_url",
            "assigned_course", "assigned_group", "assigned_teacher", "assigned_assistant_teacher"
        ]

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
            return {"id": obj.assigned_teacher.id, "full_name": obj.assigned_teacher.full_name}
        return None

    def get_assigned_assistant_teacher(self, obj):
        if obj.assigned_assistant_teacher:
            return {"id": obj.assigned_assistant_teacher.id, "full_name": obj.assigned_assistant_teacher.full_name}
        return None



