from django.urls import path
from . import views

app_name = 'chatai'

urlpatterns = [
    path('api/', views.chat_api, name='chat_api'),
    path('history/<str:session_id>/', views.get_history, name='get_history'),
    path('clear/<str:session_id>/', views.clear_history, name='clear_history'),
    path('widget-info/', views.chat_widget, name='widget_info'),
]

