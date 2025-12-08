from django.apps import AppConfig


class StudentConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student'
    verbose_name = "Students"


# agar signallar bolsa shu yerga import qilinadi

    # def ready(self):
        # signals ni shu yerga import qilamiz
        # Agar student/signals.py fayli mavjud bo'lsa
        # import student.signals  # Bu qatorni commentga oling agar signals fayli yo'q bo'lsa
##############






# class StudentConfig(AppConfig):
#     name = "students"
#     verbose_name = "Students"
#
#     def ready(self):
#         # signals ni shu yerga import qilamiz
#         import student.signals #



