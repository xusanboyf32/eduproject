from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from student.models import Student


User = get_user_model()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_student_profile_on_user_create(sender, instance: User, created, **kwargs):
    """
    Shunda yangi Student yaratilganda avto profili yaratiladi

    """
    if not created:
        return

    # Agar user = STUDENT bolsagina ishlaydi
    if getattr(instance, "role", None) !="student":
        return

    Student.objects.get_or_create(
        user=instance,
        defaults={
            "full_name": getattr(instance, "full_name", "") or "",
            "date_of_birth":getattr(instance,"date_of_birth","") or "",
            "gender": "Erkak",  # default holda
            "profiency":getattr(instance, "profiency","") or "",
            "phone_number":getattr(instance, "phone_number","") or "",
            "email":getattr(instance, "email","")or "",
            "payment":"To'lov qilmagan",
            "image":getattr(instance,"image","") or "",


        }
    )


