# authentication/views.py
import json
import secrets

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated

from .serializers import  UserSerializer


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



# =============================================================================================
#   BU BOTDAN AUTH BOLISH UHCUN VIEW MODEL BN VIEW YETARLI
# =============================================================================================

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import login as auth_login, logout
from django.utils import timezone
from .models import CustomUser, TelegramAuth


# authentication/views.py


def cleanup_expired_telegram_auth():
    """
    Faqat muddati tugagan TelegramAuth yozuvlarini o'chirish
    :return:
    """
    now = timezone.now()

    # faqat muddati tugagan yozuvlarni tugatish
    expired_count = TelegramAuth.objects.filter(expires_at__lt=now).count()
    TelegramAuth.objects.filter(expires_at__lt=now).delete()

    if expired_count > 0:
        print(f"🧹 Tozalash: {expired_count} muddati tugagan yozuv o'chirildi")

    return expired_count


# ---------------------------------------------------------------
#
@csrf_exempt
def telegram_callback(request):
    # Telegram start link GET so'rovi agar GET bo'lmasa xatolik beradi
    if request.method != "GET":
        return JsonResponse({'success':False,"message":"Noto'g'ri so'rov turi"},status=400)

    session_token = request.GET.get("token")
    code = request.GET.get("code")

    if not session_token or not code:
        return JsonResponse({"success":False,"message":"Token yoki kod topilmadi."},status=400)


    try:
        # is_used holatini e'tiborsiz qoldiramiz, faqat token va kodni tekshiramiz
        auth = TelegramAuth.objects.get(
            session_token=session_token,
            code=code,
            # *************************************
            is_used=False
            # *************************************

        )



        if auth.is_expired:
            return JsonResponse({"success":False,"message":"Kod muddatli o'tgan."},status=400)

        # Agar allaqachon ishlatilgan bo'lsa ham , muddati tugamagan bolsa ruxsat beramiz
        if auth.is_used:
            print(f"[WARNING] Auth {session_token} allaqachon ishlatilgan, lekin muddati hali tugamagan")


        try:
            # faqat mavjud Customuser
            user = CustomUser.objects.get(phone_number=auth.phone_number)

        except CustomUser.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Siz tizimda mavjud emassiz. Iltimos, admin bilan bog'laning."
            }, status=400)

        # Telegram malumotlarini yangilash
        user.telegram_id = auth.chat_id
        user.telegram_username = getattr(auth, "username", None)
        user.is_verified = True
        user.verified_at = timezone.now()
        user.save(update_fields=['telegram_id', 'telegram_username', 'is_verified', 'verified_at'])

        # Kodni ishlatilgan deb belgilash
        auth.is_used = True
        auth.save(update_fields=['is_used'])


        # user birinchi marta kirganda session yaratish
        if not request.session.session_key:
            request.session.create()
        request.session.save()
        auth_login(request, user)

        # Role bo'yicha dashboardga yo'naltirish
        role_redirects = {
            'superadmin': 'admin_dashboard',
            'admin': 'admin_dashboard',
            'student': 'student_dashboard',
            'teacher': 'teacher_dashboard',
            'high_teacher': 'high_teacher_dashboard',
            'assistant_teacher': 'assistant_teacher_dashboard',
            'Quality control': 'sifatchi_dashboard'
        }


        redirect_url = role_redirects.get(user.role)
        if redirect_url:
            return redirect(redirect_url)
        else:
            return JsonResponse({"success": False, "message": "Sizga ruxsat yo'q"}, status=403)

    except TelegramAuth.DoesNotExist:
        return JsonResponse({"success": False, "message": "Noto'g'ri kod yoki sessiya."}, status=400)




#   verify kod

@csrf_exempt
def verify_code(request):
    if request.method != "POST":
        return JsonResponse({"success":False, "message":"Noto'g'ri so'rov"})

    data = json.loads(request.body)
    code = data.get("code")
    session_token = request.session.get("login_token")

    if not session_token:
        return JsonResponse({"success": False, "message": "Sessiya yo'q. Qaytadan boshlang."})

    try:
        auth = TelegramAuth.objects.get(
            session_token=session_token,
            code=code,
            # is_used=False  # Bu qatorni olib tashlaymiz
        )

        # ***************************************
        user = CustomUser.objects.get(phone_number=auth.phone_number)
        auth_login(request, user)
        # ***************************************

        if auth.is_expired:
            return JsonResponse({"success": False, "message": "Kod muddati o'tgan."})

            # Agar allaqachon ishlatilgan bo'lsa ham, muddati tugamagan bo'lsa ruxsat beramiz
        if auth.is_used:
            print(f"[WARNING] Auth {session_token} allaqachon ishlatilgan, lekin muddati hali tugamagan")


        auth.is_used = True
        auth.save()

        if not request.session.session_key:
            request.session.create()
        request.session.save()
        user = CustomUser.objects.get(phone_number=auth.phone_number)
        auth_login(request, user)

        return JsonResponse({
            "success":True,
            "message":"Kirish amalga oshirildi",
        })

    except TelegramAuth.DoesNotExist:
        return JsonResponse({"success": False, "message": "Noto'g'ri kod."})


def login_request(request):
    # Avval keraksiz yozuvlarni ochirish
    cleanup_expired_telegram_auth()

    # 6 belgi: login_a1b2c3 (jami 12 belgi)
    session_token = "login_" + secrets.token_hex(3)  # login_ + 6 hex → 12 belgi

    TelegramAuth.objects.create(
        session_token=session_token,
        expires_at=timezone.now() + timezone.timedelta(minutes=5),
        is_used=False,
    )


    request.session['login_token'] = session_token

    bot_username = settings.TELEGRAM_BOT_USERNAME
    start_link = f"https://t.me/{bot_username}?start={session_token}"

    return render(request, 'store/login.html', {
        'telegram_link': start_link,

    })





