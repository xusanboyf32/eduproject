# # from distutils.command.install import value
#
# from asgiref.timeout import timeout
# from django.contrib.auth import get_user_model
# from django.core.cache import cache
# from rest_framework import serializers
# from rest_framework_simplejwt.exceptions import TokenBackendError
#
# from authentication.models import CustomUser, PendingUser
# from config import settings
# from django.utils import timezone
# from datetime import timedelta
# from .otp_service import OtpService
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework.exceptions import AuthenticationFailed
#
# User = get_user_model()
#
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ["id", 'first_name', 'last_name', 'phone_number', 'district', 'role', 'is_active', 'date_joined']
#         ref_name = "AuthUserSerializer" # shunda swagger yokida schema dokumentatsiyasida nomini boshqarish
#
# # =============================================================================================
# # BUNDA SERIALIZER USER OZI SIGN UP VA SIGN IN QILADI VA AGAR ADMIN HAMMANI QOSHSA BU USUL KERAK EMAS
# #==================================================================================================================
#
#
# # yangi foydalanuvchini royxatdan otkazish
# class RegisterSerializer(serializers.ModelSerializer):
#     phone_number = serializers.CharField()
#
#     class Meta:
#         model = PendingUser
#         fields = ['phone_number', 'first_name', 'last_name']
#
# # raise   ---> osha joyda dasturni to'xtatadi , bu xatolik brauzerda chiqadi
#
#     def validate_phone_number(self, value):
#         if not value.startswith("+998"):
#             raise serializers.ValidationError("Telefon raqam +998 bilan boshlanishi kerak")
#
#         if CustomUser.objects.filter(phone_number=value).exists():
#             raise serializers.ValidationError("Bu raqam bilan ro'yxatdan o'tilgan")
#         return value
#
#     def create(self, validated_data):
#         phone = validated_data['phone_number']
#         pending_user,_ = PendingUser.objects.update_or_create(
#             phone_number=phone,
#             defaults={
#                 "first_name":validated_data.get("first_name", ""),
#                 "last_name":validated_data.get("last_name",""),
#                 "role":"user",
#                 "expires_at": timezone.now() + timedelta(minutes=5),
#
#             }
#         )
#         return pending_user
#
# #  userga otp yuborish uchun kerak
# class OtpRequestSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#
#     def validate_phone_number(self,value):
#         if not value.startswith("+998"):
#             raise serializers.ValidationError("Telefon raqam +998 bilan boshlanishi kerak.")
#         if not (PendingUser.objects.filter(phone_number=value).exists()
#                 or CustomUser.objects.filter(phone_number=value).exists()):
#             raise serializers.ValidationError("Avval ro'yxatdan o'ting")
#         return value
#
#     def create(self, validated_data):
#         phone = validated_data["phone_number"]
#         otp_code = OtpService.send_otp(phone)
#         cache.set(f"otp_{phone}", otp_code, timeout=300) # 300 = 5 DAQIqa
#
#         return {
#             "message":"OTP muvaffaqiyatli yaratildi",
#             "phone_number":phone,
#             "otp":otp_code if settings.DEBUG else "****"
#         }
#
#
# # otp kodini tekshirish
# class OtpVerifySerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     code = serializers.CharField()
#
#
# # attrs  --> ma'lumotlarni lug'at ko'rinishida saqlaydi va hammasini
#     def validate(self, attrs):
#         phone = attrs.get("phone_number")
#         code = attrs.get("code")
#         cached_code = cache.get(f"otp_{phone}")
#
#         if not cached_code:
#             raise serializers.ValidationError("OTP yuborilmagan yokida mudati tugagan")
#
#         if cached_code != code:
#             raise serializers.ValidationError("Noto‘g‘ri kod.")
#
#         try:
#             pending = PendingUser.objects.get(phone_number=phone)
#         except PendingUser.DoesNotExist:
#             if not CustomUser.objects.filter(phone_number=phone).exists():
#                 raise serializers.ValidationError("Bunday raqam uchun ro‘yxatdan o‘tish topilmadi.")
#
#         attrs["pending_user"] = pending if 'pending' in locals() else None
#         return attrs
#
#     def create(self, validated_data):
#         pending = validated_data.get("pending_user")
#         phone = pending.phone_number if pending else validated_data.get("phone_number")
#
#         user, created = CustomUser.objects.get_or_create(
#             phone_number=phone,
#             defaults={
#                 "first_name": (pending.first_name if pending else ""),
#                 "last_name": (pending.last_name if pending else ""),
#                 "role": (pending.role if pending else "user"),
#                 "is_active": True,
#             }
#         )
#         return user
#
#
#
# # phone va otp kodi bn login qilish
#
# class LoginSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#     code = serializers.CharField()
#
#     def validate(self, attrs):
#         phone = attrs.get("phone_number")
#         code = attrs.get("code")
#
#         cached_otp = cache.get(f"otp_{phone}")
#         if not cached_otp:
#             raise serializers.ValidationError({"detail": "OTP muddati tugagan yoki yuborilmagan."})
#         if code != cached_otp:
#             raise serializers.ValidationError({"detail": "Noto‘g‘ri kod."})
#
#         try:
#             user = User.objects.get(phone_number=phone)
#         except User.DoesNotExist:
#             raise serializers.ValidationError({"detail": "Bunday foydalanuvchi topilmadi, oldin ro‘yxatdan o‘ting."})
#
#         attrs["user"] = user
#         return attrs
#
#
# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     # Shunda  sms kodi boladi va jwt token ichiga role, phone_number va full name qoshamiz
#     @classmethod
#     def get_token(cls,user):
#         token = super().get_token(user)
#         # Qo'shimcha claimlar
#         token['role'] = user.role
#         token['phone_number'] = user.phone_number
#         token['full_name'] = user.get_full_name()
#         return token
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#         # User haqida qo'shimcha info response'da qaytsin
#         data['user'] = {
#             "id":self.user.id,
#             "phone_number": self.user.phone_number,
#             "role": self.user.role,
#             "first_name": self.user.first_name,
#             "last_name": self.user.last_name,
#         }
#         return data
#
#
#
#
#
#
# class SifatchiLoginSerializer(TokenObtainPairSerializer):
#     # Faqar shu sifatchi kira oladi
#     @classmethod
#     def get_token(cls,user):
#         token = super().get_token(user)
#         token['role'] = user.role
#         token['phone_number'] = user.phone_number
#         return token
#
#     def validate(self, attrs):
#         data = super().validate(attrs)
#
#         # faqat sifatchi login qiladi
#         if getattr(self.user, "role", None) != "sifatchi":
#             raise AuthenticationFailed("Faqat sifat nazoratchisi login qila oladi")
#
#         data['user'] = {
#             "id":self.user_id,
#             "phone_number": self.user.phone_number,
#             "role": self.user.role,
#             "first_name": self.user.first_name,
#             "last_name": self.user.last_name,
#         }
#         return data
#
#
#
#
# ==============================================================================================================================================================================================
# ==============================================================================================================================================================================================
# ==============================================================================================================================================================================================
# ==============================================================================================================================================================================================
#
# SHUNDA ADMIN HAMMANI QOSHADI DASTURGA HUSNDA CREATE , UPDATE, DELETE YETARLI

#
#
# from rest_framework import serializers
# from .models import CustomUser
#
# class UserCreateSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#
#     class Meta:
#         model = CustomUser
#         fields = ['first_name', 'last_name', 'phone_number', 'email', 'password', 'role']
#
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = CustomUser.objects.create_user(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user
#
# class UserUpdateSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, required=False)
#
#     class Meta:
#         model = CustomUser
#         fields = ['first_name', 'last_name', 'phone_number', 'email', 'password', 'role']
#
#     def update(self, instance, validated_data):
#         password = validated_data.pop('password', None)
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         if password:
#             instance.set_password(password)
#         instance.save()
#         return instance
#
# class UserProfileSerializer(serializers.ModelSerializer):
#     """Foydalanuvchi o'z profilini ko'rishi uchun"""
#     class Meta:
#         model = CustomUser
#         fields = ['first_name', 'last_name', 'phone_number', 'email', 'role']
#         read_only_fields = ['role', 'phone_number']








#====================================================================================================
#  Shunda phone_number bilan admin qoshadi
# ================================================================================================================================================
# from rest_framework import serializers
# from .models import CustomUser
#
#
# # ---------------- Admin user yaratish serializer ----------------
# class AdminCreateUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['phone_number']
#
#     def create(self, validated_data):
#         # Admin tomonidan user yaratish
#         return CustomUser.objects.create_user(
#             phone_number=validated_data['phone_number'],
#             created_by='admin'
#         )
#
#
# # ---------------- Login serializer (faqat phone_number) ----------------
# class PhoneLoginSerializer(serializers.Serializer):
#     phone_number = serializers.CharField()
#
#     def validate(self, data):
#         phone = data.get("phone_number")
#         try:
#             user = CustomUser.objects.get(phone_number=phone)
#         except CustomUser.DoesNotExist:
#             raise serializers.ValidationError("Bunday telefon raqam topilmadi")
#
#         # validated_data ichiga userni qo‘shamiz
#         data['user'] = user
#         return data
#


# ==========================================================================================
#  SERIALIZER BOTDAN XABAR KELADIGAN QILIB
# ==========================================================================================

# authentication/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import CustomUser, VerificationCode


class UserSerializer(serializers.ModelSerializer):
    """
    Vazifa: User ma'lumotlarini API ga chiqarish
    Natija: Frontend user haqida ma'lumot oladi
    """

    class Meta:
        model = CustomUser
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'role',
            'group', 'course', 'subject', 'is_verified', 'date_joined'
        ]
        read_only_fields = ['is_verified', 'date_joined']


class TelegramLoginSerializer(serializers.Serializer):
    """
    Vazifa: Telegram botdan kelgan ma'lumotlarni validatsiya qilish
    Natija: Telefon raqam va Telegram ID bir-biriga bog'lanadi
    """
    phone_number = serializers.CharField(max_length=20)
    telegram_id = serializers.IntegerField()
    telegram_username = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, data):
        # 1. Telefon raqam admin yaratganmi?
        try:
            user = CustomUser.objects.get(phone_number=data['phone_number'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError(
                "Bu telefon raqam ro'yxatdan o'tmagan. Admin bilan bog'laning."
            )

        # 2. Agar allaqachon telegram_id biriktirilgan bo'lsa
        telegram_id = data['telegram_id']
        if user.telegram_id and user.telegram_id != telegram_id:
            raise serializers.ValidationError(
                "Bu telefon raqam boshqa Telegram akkauntga biriktirilgan."
            )

        # 3. Agar birinchi marta kirsa, telegram ma'lumotlarini saqlash
        if not user.telegram_id:
            user.telegram_id = telegram_id
            user.telegram_username = data.get('telegram_username', '')
            user.save()

        data['user'] = user
        return data


class VerifyCodeSerializer(serializers.Serializer):
    """
    Vazifa: Foydalanuvchi kiritgan kodni tekshirish
    Natija: Kod to'g'ri bo'lsa, user login qiladi
    """
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        phone = data['phone_number']
        code = data['code']

        # 1. User borligini tekshirish
        try:
            user = CustomUser.objects.get(phone_number=phone)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Foydalanuvchi topilmadi")

        # 2. Oxirgi yaratilgan kodni topish
        verify_code = VerificationCode.objects.filter(
            user=user,
            is_used=False
        ).order_by('-created_at').first()

        if not verify_code:
            raise serializers.ValidationError("Kod topilmadi yoki ishlatilgan")

        # 3. Kodning muddati o'tmaganligini tekshirish
        if timezone.now() > verify_code.expires_at:
            raise serializers.ValidationError("Kodning muddati o'tgan")

        # 4. Kodni tekshirish
        if not verify_code.verify(code):
            raise serializers.ValidationError("Noto'g'ri kod")

        # 5. User ni tasdiqlash
        user.is_verified = True
        user.verified_at = timezone.now()
        user.last_login = timezone.now()
        user.save()

        data['user'] = user
        return data



