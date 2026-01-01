from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentProfileViewSet,

    StudentDashboardView,
    StudentGroupInfoView
)

router = DefaultRouter()
router.register(r'profile', StudentProfileViewSet, basename='student-profile')

urlpatterns = [
    # ViewSetlar router orqali
    path('', include(router.urls)),



    # Dashboard
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),

    # Group info
    path('group-info/', StudentGroupInfoView.as_view(), name='student-group-info'),
]
