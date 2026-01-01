from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .models import SifatchiProfile
from .views import (
    CourseViewSet,
    HighTeacherViewSet,
    AssistantTeacherViewSet,
    GroupViewSet,
    TaskViewSet,
    StudentVideoListView,
    NotionURLViewSet, TeacherCommentViewSet, KnescopeVideoUrlViewSet, SifatchiProfileViewSet
)

# ------------------ Router yaratish ------------------
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'high-teachers', HighTeacherViewSet, basename='highteacher')
router.register(r'assistant-teachers', AssistantTeacherViewSet, basename='assistantteacher')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'notion', NotionURLViewSet,basename='notionurl')
router.register(r'comment',TeacherCommentViewSet, basename='comment')
router.register(r'kinescope', KnescopeVideoUrlViewSet, basename='kinescopeurl')
router.register(r'sifatchi',SifatchiProfileViewSet,basename='sifatchi-profile')

from authentication.views import telegram_callback

# ------------------ URL patterns ------------------
urlpatterns = [
    # Router orqali avtomatik CRUD URL-lar
    path('', include(router.urls)),

    # Talaba uchun video ro'yxati
    path('student/videos/', StudentVideoListView.as_view(), name='student-video-list'),

    # Talaba vazifa yuklash (SubmitTaskView)

    path('auth/telegram/callback/', telegram_callback, name='telegram_callback')

]

