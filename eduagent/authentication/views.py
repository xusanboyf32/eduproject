# authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login
from django.middleware.csrf import get_token

from .models import CustomUser, VerificationCode
from .serializers import TelegramLoginSerializer, VerifyCodeSerializer, UserSerializer


class TelegramLoginView(APIView):
    """
    Vazifa: Telegram botdan kelgan so'rovni qabul qilish
    Natija: Yangi kod yaratiladi va botga qaytariladi
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TelegramLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            telegram_id = serializer.validated_data['telegram_id']

            # Yangi kod yaratish
            verify_code = VerificationCode.create_code(
                user=user,
                telegram_id=telegram_id
            )

            return Response({
                'success': True,
                'code': verify_code.code,  # Botga yuboriladi
                'message': 'Kod yaratildi va telegramga yuborildi'
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    """
    Vazifa: Foydalanuvchi kiritgan kodni tekshirish
    Natija: Kod to'g'ri bo'lsa, session ochiladi
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Django session login
            login(request, user)

            # CSRF token yaratish
            csrf_token = get_token(request)

            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'csrf_token': csrf_token,
                'redirect_url': self._get_redirect_url(user.role)
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _get_redirect_url(self, role):
        urls = {
            CustomUser.ROLE_STUDENT: '/dashboard/student/',
            CustomUser.ROLE_TEACHER: '/dashboard/teacher/',
            CustomUser.ROLE_ASSISTANT: '/dashboard/assistant/',
            CustomUser.ROLE_HIGH: '/dashboard/high/',
            CustomUser.ROLE_ADMIN: '/admin/',
            CustomUser.ROLE_SUPERADMIN: '/admin/',
        }
        return urls.get(role, '/')


class CheckAuthView(APIView):
    """
    Vazifa: User login qilganmi tekshirish
    Natija: Frontend user holatini biladi
    """

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': UserSerializer(request.user).data
            })
        return Response({'authenticated': False})


class LogoutView(APIView):
    """
    Vazifa: User ni logout qilish
    Natija: Session tozalanishi
    """

    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        return Response({'success': True, 'message': 'Logged out'})


# ==================== ADMIN VIEWS ====================
class AdminCreateUserView(APIView):
    """
    Vazifa: Admin yangi user yaratish
    Natija: Parolsiz user yaratiladi
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Faqat adminlar user yarata oladi
        if request.user.role not in [CustomUser.ROLE_ADMIN, CustomUser.ROLE_SUPERADMIN]:
            return Response(
                {'error': 'Ruxsat yo\'q'},
                status=status.HTTP_403_FORBIDDEN
            )

        phone_number = request.data.get('phone_number')
        role = request.data.get('role', CustomUser.ROLE_STUDENT)
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not phone_number:
            return Response(
                {'error': 'Telefon raqam kiritilishi kerak'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # User yaratish (PAROL BERILMAYDI!)
        try:
            user = CustomUser.objects.create_user(
                phone_number=phone_number,
                role=role,
                first_name=first_name,
                last_name=last_name
            )

            return Response({
                'success': True,
                'message': f'Foydalanuvchi yaratildi: {phone_number}',
                'user': UserSerializer(user).data
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )