from django.contrib import admin
from .models import UserActivity


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'activity_type', 'created_at', 'related_object']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'content_type', 'object_id']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')