# from django.conf import settings
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
#
# from course.models import High_Teacher, Assistant_Teacher
# from student.models import Student
#
# User = get_user_model()
#
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
# def create_profiles(sender, instance: User, created, **kwargs):
#     if not created:
#         return
#
#     # STUDENT profili
#     if instance.role == "student":
#         Student.objects.get_or_create(
#             user=instance,
#             defaults={
#                 "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
#                 "phone_number": instance.phone_number,
#             }
#         )
#
#     # HIGH TEACHER profili
#     elif instance.role == "high_teacher":
#         High_Teacher.objects.get_or_create(
#             user=instance,
#             defaults={
#                 "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
#                 "phone_number": instance.phone_number,
#             }
#         )
#
#     # ASSISTANT TEACHER profili
#     elif instance.role == "assistant_teacher":
#         Assistant_Teacher.objects.get_or_create(
#             user=instance,
#             defaults={
#                 "full_name": f"{instance.first_name or ''} {instance.last_name or ''}".strip(),
#                 "phone_number": instance.phone_number,
#             }
#         )


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



