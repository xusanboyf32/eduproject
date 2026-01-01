


#  --------------------------- NEW VIEWS BU YANGI VERSIYADAGI GEMINI -----------------------------

# chatai/views.py - FAQLAT YANGI VERSIYA
import json
from google import genai  # Yangi import
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
import os
from dotenv import load_dotenv
from .models import ChatSession, ChatMessage

load_dotenv()

# API kalitni .env dan olish
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


@csrf_exempt
@require_POST
def chat_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default_session')

        if not message:
            return JsonResponse({'success': False, 'error': 'Xabar bo\'sh'}, status=400)

        if not GEMINI_API_KEY:
            return JsonResponse({'success': False, 'error': 'API kalit topilmadi'}, status=500)

        with transaction.atomic():
            # Session ni database da saqlash
            session, created = ChatSession.objects.get_or_create(
                session_id=session_id,
                defaults={'created_at': timezone.now()}
            )

            # Kontekst uchun avvalgi xabarlar
            recent_messages = ChatMessage.objects.filter(
                session=session
            ).order_by('-timestamp')[:3]

            context_lines = []
            for msg in reversed(recent_messages):
                context_lines.append(f"User: {msg.user_message}")
                context_lines.append(f"AI: {msg.ai_response}")

            context = "\n".join(context_lines) if context_lines else "Yangi suhbat."

            prompt = f"""
            {context}

            Yangi savol: {message}

            Javobni faqat o'zbek tilida bering. Qisqa va aniq bo'lsin.
            """

            # YANGI USUL: google-genai bilan ishlash
            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )

            ai_response = response.text.strip()

            # Database ga saqlash
            ChatMessage.objects.create(
                session=session,
                user_message=message,
                ai_response=ai_response
            )

            session.updated_at = timezone.now()
            session.save()

            return JsonResponse({
                'success': True,
                'response': ai_response,
                'session_id': session_id
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)[:100],
            'response': 'Xatolik yuz berdi. Keyinroq urinib ko\'ring.'
        }, status=500)


def get_history(request, session_id):
    """Suhbat tarixini olish"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = ChatMessage.objects.filter(
            session=session
        ).order_by('timestamp')

        history = []
        for msg in messages:
            history.append({
                'id': msg.id,
                'user': msg.user_message,
                'ai': msg.ai_response,
                'time': msg.timestamp.strftime('%H:%M, %d.%m.%Y'),
                'timestamp': msg.timestamp.isoformat()
            })

        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'total': messages.count(),
            'history': history,
            'updated_at': session.updated_at.isoformat()
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'total': 0,
            'history': [],
            'message': 'Session topilmadi'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)[:200]
        }, status=500)


@csrf_exempt
@require_POST
def clear_history(request, session_id):
    """Suhbat tarixini tozalash"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        count = ChatMessage.objects.filter(session=session).count()
        ChatMessage.objects.filter(session=session).delete()
        session.delete()

        return JsonResponse({
            'success': True,
            'message': f'{count} ta xabar o\'chirildi',
            'session_id': session_id
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Session topilmadi'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)[:200]
        }, status=500)


def chat_widget(request):
    """Chat widget uchun alohida sahifa"""
    return JsonResponse({
        'widget': True,
        'endpoints': {
            'chat': '/ai/api/',
            'history': '/ai/history/{session_id}/',
            'clear': '/ai/clear/{session_id}/'
        }
    })

