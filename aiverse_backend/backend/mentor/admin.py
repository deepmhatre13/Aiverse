from django.contrib import admin
from .models import MentorSession, MentorMessage


@admin.register(MentorSession)
class MentorSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'last_active_at', 'message_count']
    list_filter = ['created_at', 'last_active_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'last_active_at']
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(MentorMessage)
class MentorMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'session__user__email']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'