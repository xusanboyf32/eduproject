# authentication/signals.py

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from course.models import High_Teacher, Assistant_Teacher

User = get_user_model()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_teacher_profiles(sender, instance: User, created, **kwargs):
    """
    Foydalanuvchi yaratildi → agar u High_Teacher yoki Assistant_Teacher bo'lsa,
    avtomatik profil yaratadi.
    """
    if not created:
        return

    # Agar user role = 'high_teacher'
    if getattr(instance, "role", None) == "high_teacher":
        High_Teacher.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": getattr(instance, "full_name", "") or "",
                "date_of_birth":getattr(instance, "date_of_birth","")or "",
                "gender": "Erkak",
                "phone_number": getattr(instance, "phone_number", "") or "",
                "email": getattr(instance, "email", "") or "",
                "job": "",
                "experience_year": 0,
                "info_knowladge": "",
                "image":getattr(instance, "image","") or "",
            }
        )

    # Agar user role = 'assistant_teacher'
    elif getattr(instance, "role", None) == "assistant_teacher":

        full_name = f"{instance.first_name or ''} {instance.last_name or ''}".strip()

        Assistant_Teacher.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": full_name,
                "date_of_birth": getattr(instance, "date_of_birth", "") or "",
                "gender": "Erkak",
                "phone_number": getattr(instance, "phone_number", "") or "",
                "email": getattr(instance, "email", "") or "",
                "job": "",
                "experience_year": 0,
                "info_knowladge": "",
                "image": getattr(instance, "image", "") or "",

            }
        )
