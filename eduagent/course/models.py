from django.core.validators import MaxLengthValidator, URLValidator
from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings

from authentication.models import CustomUser


# KURSLAR BOLADI VA BU KURSLARGA TEGISGLI GROUPLAR VA UNGA TEGISGLI TALABALAR BOLADI
#---------------------------------------------------------------------
class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name='Kurs nomi',unique=True)
    description = models.TextField(blank=True, verbose_name="Kurs haqida tavsifi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name= "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ['name']

    def __str__(self):
        return self.name


# katta techar , kichik teacher , sifatchi, admin , yordamchi admin (agar bular kk bolsa)




#----------------------------------------------------------------
# Eng katta ustoz modeli (Komiljon aka)
class High_Teacher(models.Model):
    GENDER_CHOICES = [("Erkak", "Erkak"), ("Ayol", "Ayol")]


    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # <-- O'ZGARTIRISH
        on_delete=models.CASCADE,
        related_name="high_teacher_profile"
    )

    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    job = models.CharField(max_length=250)
    experience_year = models.IntegerField(default=0)
    info_knowladge = models.TextField(validators=[MaxLengthValidator(1000)])
    image = models.ImageField(upload_to='ustozrasm/', null=True, blank=True)



    class Meta:
        verbose_name = 'Katta Ustoz'
        verbose_name_plural = 'Katta Ustozlar'

    def __str__(self):
        return self.full_name


#-------------------------------------------------------------
class Assistant_Teacher(models.Model):
    GENDER_CHOICES = [("Erkak", "Erkak"), ("Ayol", "Ayol")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # <-- User o'rniga settings.AUTH_USER_MODEL
        on_delete=models.CASCADE,
        related_name="assistant_teacher_profile"
    )

    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    job = models.CharField(max_length=250)
    experience_year = models.IntegerField(default=0)
    info_knowladge = models.TextField(validators=[MaxLengthValidator(1000)])
    image = models.ImageField(upload_to='ustozrasm/', null=True, blank=True)




    class Meta:
        verbose_name = 'Yordamchi Ustoz'
        verbose_name_plural = "Yordamchi Ustozlar"

    def __str__(self):
        return self.full_name



#-------------------------------------------------------#
#-----------------------------------------------------------------
class Group(models.Model):

    name = models.CharField(max_length=100, verbose_name="Guruh nomi")


    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='courses_groups',
        verbose_name='Kurs'
    )

    # katta ustoz kop guruhlarga bolishi uchun
    main_teacher = models.ForeignKey(
        High_Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="main_teacher_groups",
        verbose_name="Asosiy ustoz"
    )

    assistant_teacher = models.ManyToManyField(
        Assistant_Teacher,
        related_name='assistant_teacher',
        blank=True,
        verbose_name='Yordamchi ustozlar'
    )




    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ["course", 'name']
        unique_together = ['course', 'name']

    def __str__(self):
        return f"{self.course.name} - {self.name}"




# --------------------------------------------------------------------
# KINESCOPE DAN TOLAQONLI FREE VERSIONDA FOYDALAISHDA ADMIN PANELDAN FOYDALANISH
# --------------------------------------------------------------------


class KnescopeVideoUrl(models.Model):
    title = models.CharField(max_length=255)
    kinescope_video_link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return self.title




#-----------------------------------  YANGI TASK MODELI -----------------------------------
# models.py - Task modelini o'zgartiramiz

class Task(models.Model):
    # video_lesson = models.ForeignKey("course.VideoLesson", on_delete=models.CASCADE, related_name='tasks')

    # VIDEODAN KINESKOPEGA BOGLADIK
    kinescope_video = models.ForeignKey(
        "course.KnescopeVideoUrl",
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True

    )
    student = models.ForeignKey(
        "student.Student",
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    assistant_teacher = models.ForeignKey(
        'course.Assistant_Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    title = models.CharField(max_length=30)
    submitted_file = models.FileField(upload_to='student_tasks/', null=True, blank=True)

    # Vazifa holati (status)
    STATUS_CHOICES = [
        ('yuklandi', 'Yuklandi'),
        ('baholandi', 'Baholandi'),

    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='yuklandi'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vazifa"
        verbose_name_plural = "Vazifalar"
        ordering = ['-created_at']

    def __str__(self):
        video_title = self.kinescope_video.title if self.kinescope_video else "No video"
        return f"{self.student.full_name} -{self.title}- {video_title}"





#--------------------------   NOTION UCHUN ALOHIDA MODEL KERAK  ------------------------------------

class NotionURL(models.Model):
    main_teacher = models.ForeignKey(
        High_Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notion_main_teacher_groups",
        verbose_name="Asosiy ustoz"
    )

    assistant_teacher = models.ManyToManyField(
        Assistant_Teacher,
        related_name='notion_assistant_teacher',
        blank=True,
        verbose_name='Yordamchi ustozlar'
    )


    title = models.CharField(max_length=200)

    notion_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        verbose_name="Ustoz Notion URL",
        help_text="Ustozning Notion sahifasi linki"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.main_teacher} - {self.title}"


# -----------------------  NEW TEACHER COMMENT ------------------------------------

class TeacherComment(models.Model):
    # Baho tanlovlari - 1 dan 5 gacha
    SCORE_CHOICES = [
        (1, '1 - Qoniqarsiz'),
        (2, '2 - Qoniqarli'),
        (3, '3 - Yaxshi'),
        (4, '4 - Juda yaxshi'),
        (5, '5 - A\'lo'),
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='teacher_comments',
        verbose_name='Vazifa'
    )

    assistant_teacher = models.ForeignKey(
        Assistant_Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assistant_teacher_comment",
        verbose_name="Yozgan Ustoz"
    )

    comment = models.TextField(verbose_name='Komentariya')

    # ✅ YANGI: Score maydoni faqat TeacherComment da
    score = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Baho',
        choices=SCORE_CHOICES,
        help_text="1 dan 5 gacha baholang"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        # Har bir vazifa uchun har bir assistant teacher faqat bir marta baho qo'yishi mumkin
        unique_together = ['task', 'assistant_teacher']

    def __str__(self):
        score_text = f" - Baho: {self.get_score_display()}" if self.score else ""
        return f"Task ID:{self.task.id} - {self.assistant_teacher}{score_text}"




#============================================================================
#  BU SIFATCHI MODEL
#============================================================================
class SifatchiProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='Sifatchi_profile',
        verbose_name="Sifat_Nazoratchi"
    )
    full_name = models.CharField(max_length=255, verbose_name="To'liq ismi")

    # rasmi
    image = models.ImageField(
        upload_to="sifatchi_images/",
        blank=True,
        null=True,
        verbose_name='Profil rasmi'
    )

# employee_id si boladi har bir operatorda masalan ismi familiyasi bir xil bolsa ham ID si farq qiladi
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Sifatchi ID",
        help_text='Masalan: "SP_001"'

    )

    department = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Bo'lim"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Telefon')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')


    class Meta:
        verbose_name = 'Sifatchi Profili'
        verbose_name_plural = 'Sifatchi Profillari'
        ordering = ["-created_at"]
        db_table = 'authentication_operator_profile'

        def __str__(self):
            return f"{self.full_name} {self.employee_id}"



