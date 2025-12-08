from django.core.validators import MaxLengthValidator, URLValidator
from django.db import models
from django.core.validators import FileExtensionValidator

from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from django.conf import settings


# from student.models import Student

# User = get_user_model()


# KURSLAR BOLADI VA BU KURSLARGA TEGISGLI GROUPLAR VA UNGA TEGISGLI TALABALAR BOLADI
#---------------------------------------------------------------------
class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name='Kurs nomi', )
    description = models.TextField(blank=True, verbose_name="Kurs haqida tavsifi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name= "Kurs"
        verbose_name_plural = "Kurslar"
        ordering = ['name']

    def __str__(self):
        return self.name

    # User = get_user_model()

# katta techar , kichik teacher , sifatchi, admin , yordamchi admin (agar bular kk bolsa)

#----------------------------------------------------------------
# Eng katta ustoz modeli (Koniljon aka)
class High_Teacher(models.Model):
    GENDER_CHOICES = [("Erkak", "Erkak"), ("Ayol", "Ayol")]

    # User = get_user_model()
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="high_teacher_profile")

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

    # notion uchun url qoshish
    notion_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        verbose_name="Ustoz Notion URL",
        help_text="Ustozning Notion sahifasi linki"
    )

    class Meta:
        verbose_name = 'Katta Ustoz'
        verbose_name_plural = 'Katta Ustozlar'

    def __str__(self):
        return self.full_name


#-------------------------------------------------------------
class Assistant_Teacher(models.Model):
    GENDER_CHOICES = [("Erkak", "Erkak"), ("Ayol", "Ayol")]
    # user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="assistant_teacher_profile")

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

#-----------------------------------------------------------------------

class VideoLesson(models.Model):
    title = models.CharField(max_length=255, verbose_name="Video sarlavhasi")
    description = models.TextField(blank=True, verbose_name="Video tavsifi")

    # Fayl maydoni
    video_file = models.FileField(
        upload_to='video_lessons/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4','avi','mov','mkv'])],
        verbose_name='Video fayli'

    )

    course = models.ManyToManyField(
        Course,
        related_name="video_lessons",
        verbose_name="Kurs"
    )

    group = models.ManyToManyField(
        Group,
        related_name='video_lessons',
        blank=True,
        verbose_name='Guruhlar',
        help_text="Agar hech qaysi guruh tanlanmasa , barcha guruhlar ko'rinadi"
    )

    duration = models.DurationField(null=True, blank=True,verbose_name="Video davomiyligi")
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="Fayl hajmi (bayt)")

    from authentication.models import SifatchiProfile


    uploaded_by = models.ForeignKey(
        'authentication.SifatchiProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_videos',
        verbose_name='Yuklagan sifatchi'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqti')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')

    class Meta:
        verbose_name = "Video Darslik"
        verbose_name_plural = "Video Darsliklar"
        ordering = ['-created_at']
        db_table = "content_video_lesson"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Fayl hajmini hisoblash
        if self.video_file and not self.file_size:
            self.file_size = self.video_file.size
        super().save(*args, **kwargs)



# TALABA VAZIFA YUKLASIN

class Task(models.Model):
    video_lesson = models.ForeignKey("course.VideoLesson", on_delete=models.CASCADE, related_name='tasks')
    student = models.ForeignKey("student.Student", on_delete=models.CASCADE, related_name='tasks')
    assistant_teacher = models.ForeignKey('course.Assistant_Teacher', on_delete=models.SET_NULL, null=True, blank=True)

    submitted_file = models.FileField(upload_to='student_tasks/', null=True, blank=True)
    comment = models.TextField(blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)  # baho

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vazifa"
        verbose_name_plural = "Vazifalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.video_lesson.title}"


    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #


