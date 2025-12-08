# YANA HAM YANGI AUTH


# authentication/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import hashlib
import secrets
import random


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


# ==================== VERIFICATION CODE ====================
class VerificationCode(models.Model):
    """
    Vazifa: Telegramga yuboriladigan kodlarni saqlash
    Natija: Har bir kirish uchun yangi kod, 1 daqiqa amal qiladi
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="verification_codes")
    phone_number = models.CharField(max_length=20, db_index=True)
    telegram_id = models.BigIntegerField()
    code = models.CharField(max_length=6)  # Telegramga yuboriladi
    code_hash = models.CharField(max_length=128)  # Database da hashed saqlanadi

    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["phone_number", "is_used"]),
            models.Index(fields=["telegram_id", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]
        ordering = ["-created_at"]

    @staticmethod
    def generate_code():
        """6 xonali random kod"""
        return f"{random.randint(100000, 999999)}"

    @staticmethod
    def hash_code(code):
        """Kodni SHA256 orqali hash qilish"""
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def create_code(cls, user, telegram_id):
        """Yangi verify code yaratish"""
        # Eski kodlarni o'chirish
        cls.objects.filter(
            user=user,
            is_used=False,
            expires_at__gt=timezone.now()
        ).delete()

        # Yangi kod yaratish
        code = cls.generate_code()
        expires_at = timezone.now() + timezone.timedelta(minutes=1)  # 1 daqiqa

        return cls.objects.create(
            user=user,
            phone_number=user.phone_number,
            telegram_id=telegram_id,
            code=code,
            code_hash=cls.hash_code(code),
            expires_at=expires_at
        )

    def verify(self, input_code):
        """Kodni tekshirish"""
        if self.is_used or timezone.now() > self.expires_at:
            return False

        input_hash = self.hash_code(input_code)
        if secrets.compare_digest(self.code_hash, input_hash):
            self.is_used = True
            self.save()
            return True
        return False





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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now_add=True, verbose_name='Yangilangan vaqt')


    class Meta:
        verbose_name = 'Sifatchi Profili'
        verbose_name_plural = 'Sifatchi Profillari'
        ordering = ["-created_at"]
        db_table = 'authentication_operator_profile'

        def __str__(self):
            return f"{self.full_name} {self.employee_id}"



