from django.db import models
from django.conf import settings
from course.models import Group,  Course, Assistant_Teacher
from django.contrib.auth import get_user_model

from course.models import High_Teacher

User = get_user_model()


class Student(models.Model):
    STUDY_BEFORE = [("Dasturlashdan umuman xabarim yo'q", "Dasturlashdan umuman xabarim yo'q"), ("Komputer savodxonligini bilaman(Word, Excel, Filelar bn ishlay olaman)","Dasturlashni yaxshi bilaman qo'shimcha o'qimoqchiman")]
    PAYMENT_CHOICES = [("To'lov qilingan", "To'lov qilingan"),("To'lov qilinmagan", "To'lov qilinmagan")]
    GENDER_CHOICES = [("Erkak", "Erkak"), ("Ayol", "Ayol")]


    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=50, choices=GENDER_CHOICES)
    profiency = models.CharField(max_length=100, choices=STUDY_BEFORE)  #profiency -> bilish darajasi study before ga bogliq
    phone_number = models.CharField(max_length=20,unique=True)
    email = models.EmailField(blank=True)
    payment = models.CharField(max_length=100, choices=PAYMENT_CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT, related_name="created_student", null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    # --------IMAGE degani ni pro verdiyaga o'tkazamiz
    image = models.ImageField(upload_to="students/images/%Y/%m/%d/", blank=True, null=True, verbose_name="Rasm")
    #-- ---------------------------------------------------------------------
    # image = models.ImageField(upload_to="images/", blank=True, null=True)
    """BU RASM YUKLASH UCHUN """

    def save(self, *args, **kwargs):
        # agar hali rasm yuklamasa default rasm qoyiladi
        if not self.image:
            if self.gender == "Erkak":
                self.image = "images/default_mail.png"
            else:
                self.image = "images/default_female.png"
        super().save(*args, **kwargs)  # user django asl save funkisyasini chiariadi hamma narsa save boladi bazaga


    assigned_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        related_name='course_students',
        verbose_name='Kursga tegishli talabalar',
        null=True,
        blank=True
    )

    # groupdan foreignkey
    assigned_group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="group_students",
        verbose_name='Guruhga tegishli talabalar',
        null=True,
        blank=True
    )

# ---------------------------------------------------------


    # bir necha oquvchi bir necha ustozga bogliq ekanligi
    assigned_teacher = models.ForeignKey(
        High_Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="High_teacher_students",
        verbose_name="Biriktirilgan hamkor",
        help_text="Operator tomonidan tanlanadi"

    )

    assigned_assistant_teacher = models.ForeignKey(
        Assistant_Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assistant_students',
        verbose_name='Yordamchi ustoz'

    )

    # qoshilgan sanasi
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt",
        help_text = "Bemor qachon yaratilgan"
    )

    # update qilingan vaqti \
    updated_at = models.DateTimeField(
        auto_now = True,  # tahrilaganda yangi vaqt bilan ozgarganda 'now' true bo'ladi
        verbose_name="Yangilangan vaqt",
        help_text="Oxirgi yangilangan vaqt"
    )


    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
        ordering = ["-created_at"]
        db_table = "students_student"

    def __str__(self):
        return self.full_name



# =============================================================================================
# Student History modeli
# =============================================================================================
class StudentHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="history")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]



