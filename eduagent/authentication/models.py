# YANA HAM YANGI AUTH

# BU MENING OXIRGI VARIANT SIFATIDA QILINGAN KODIM FAQAT GET BOR EDI



# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


# ==================== USER MANAGER ====================
class CustomUserManager(BaseUserManager):
    """
    Vazifa: Admin yangi user yaratish
    Natija: Parolsiz user yaratiladi (faqat Telegram orqali kiriladi)
    """

    def create_user(self, phone_number,role=None, **extra_fields):
        if not phone_number:
            raise ValueError("Telefon raqam kerak")

        # Telefon raqamni to'g'ri formatga keltirish
        phone = str(phone_number).strip()
        if not phone.startswith('+998'):
            phone = '+998' + phone.lstrip('998')

        # ========================================================================
        #Bu kod role qoshamiz shunda role bilan yaratila oladi
        # Role ni qo'shish
        if role:
            extra_fields['role'] = role
        # ========================================================================

        user = self.model(phone_number=phone, **extra_fields)
        user.set_unusable_password()  # PAROL ISHLATILMAYDI
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', CustomUser.ROLE_SUPERADMIN)
        # extra_fields.setdefault('role', 'superadmin')

        if password is None:
            raise ValueError("Superuser uchun parol berish shart")

        user = self.create_user(phone_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user



# ==================== USER MODEL ====================
class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Vazifa: Barcha foydalanuvchilarni saqlash
    Natija: Har bir user uchun profil yaratiladi
    """
    # Rollar
    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_ASSISTANT = "assistant_teacher"
    ROLE_HIGH = "high_teacher"
    ROLE_ADMIN = "admin"
    ROLE_SUPERADMIN = "superadmin"
    ROLE_SIFATCHI = "Quality control"

    ROLE_CHOICES = [
        (ROLE_STUDENT, "Talaba"),
        (ROLE_TEACHER, "Ustoz"),
        (ROLE_ASSISTANT, "Yordamchi ustoz"),
        (ROLE_HIGH, "Katta ustoz"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_SUPERADMIN, "Super Admin"),
        (ROLE_SIFATCHI , "Sifatchi")
    ]


    # ========== ADMIN YARATADI ==========
    # Admin panel orqali to'ldiriladi
    phone_number = models.CharField(max_length=20, unique=True, verbose_name="Telefon raqam")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ism")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Familiya")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT, verbose_name="Rol")

    # ========== USER TELEGRAM ORQALI KIRGANDA ==========
    telegram_id = models.BigIntegerField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Telegram ID",
        help_text="User birinchi marta Telegram orqali kirganda avtomatik biriktiriladi"
    )
    telegram_username = models.CharField(max_length=100, blank=True, null=True, verbose_name="Telegram username")
    is_verified = models.BooleanField(default=False, verbose_name="Tasdiqlangan")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Tasdiqlangan vaqt")

    # ========== TIZIM ==========
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_staff = models.BooleanField(default=False, verbose_name="Staff")
    is_superuser = models.BooleanField(default=False, verbose_name="Superuser")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Oxirgi kirish")

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
        ordering = ["-date_joined"]

    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"{name} ({self.phone_number})" if name else self.phone_number





#  Telegram botdan auth uchun  model
class TelegramAuth(models.Model):
    session_token = models.CharField(max_length=12, unique=True, null=True)  # QO'SHILDI!
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    code = models.CharField(max_length=6, blank=True, null=True)
    chat_id = models.TextField(default='default_id')
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at




