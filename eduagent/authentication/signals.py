
# Customuser modeliga togri ulangan shunda admin panelda user  yaratilganda
# avtomatik yaratiladi


from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

from student.models import Student
from course.models import High_Teacher, Assistant_Teacher

@receiver(post_save, sender=CustomUser)
def create_profiles(sender, instance: CustomUser, created, **kwargs):
    if not created:
        return

    # Student profile
    if instance.role == CustomUser.ROLE_STUDENT:
        Student.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
                "phone_number": instance.phone_number,
            }
        )

    # High Teacher profile
    elif instance.role == CustomUser.ROLE_HIGH:
        High_Teacher.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
                "phone_number": instance.phone_number,
            }
        )

    # Assistant Teacher profile
    elif instance.role == CustomUser.ROLE_ASSISTANT:
        Assistant_Teacher.objects.get_or_create(
            user=instance,
            defaults={
                "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
                "phone_number": instance.phone_number,
            }
        )



