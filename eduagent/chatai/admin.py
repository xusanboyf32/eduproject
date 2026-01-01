from django.contrib import admin
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'created_at', 'updated_at', 'message_count')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('session_id',)
    readonly_fields = ('created_at', 'updated_at')

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Xabarlar soni'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'user_message_short', 'ai_response_short', 'created_at')
    list_filter = ('created_at', 'session')
    search_fields = ('user_message', 'ai_response', 'session__session_id')
    readonly_fields = ('created_at',)

    def user_message_short(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message

    user_message_short.short_description = 'Foydalanuvchi xabari'

    def ai_response_short(self, obj):
        return obj.ai_response[:50] + '...' if len(obj.ai_response) > 50 else obj.ai_response

    ai_response_short.short_description = 'AI javobi'

