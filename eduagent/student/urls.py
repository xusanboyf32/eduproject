from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentProfileViewSet,
    StudentVideoListView,
    StudentVideoDetailView,
    StudentTaskViewSet,
    SubmitTaskView,
    StudentDashboardView,
    StudentGroupInfoView
)

router = DefaultRouter()
router.register(r'profile', StudentProfileViewSet, basename='student-profile')
router.register(r'tasks', StudentTaskViewSet, basename='student-tasks')

urlpatterns = [
    # ViewSetlar router orqali
    path('', include(router.urls)),

    # Videos
    path('videos/', StudentVideoListView.as_view(), name='student-videos-list'),
    path('videos/<int:video_id>/', StudentVideoDetailView.as_view(), name='student-video-detail'),

    # Submit task
    path('submit-task/', SubmitTaskView.as_view(), name='submit-task-list'),  # get bilan barcha vazifalar
    path('submit-task/<int:video_id>/', SubmitTaskView.as_view(), name='submit-task'),

    # Dashboard
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),

    # Group info
    path('group-info/', StudentGroupInfoView.as_view(), name='student-group-info'),
]
