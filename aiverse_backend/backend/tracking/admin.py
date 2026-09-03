from django.contrib import admin
from .models import LearnerEvent


@admin.register(LearnerEvent)
class LearnerEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'content_type', 'timestamp')
    list_filter = ('event_type', 'content_type', 'timestamp')
    search_fields = ('user__username',)
    readonly_fields = ('id', 'timestamp')
