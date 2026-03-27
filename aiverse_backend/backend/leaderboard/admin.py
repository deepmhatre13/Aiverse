from django.contrib import admin
from .models import LeaderboardEntry, LeaderboardEvent


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ['rank', 'user', 'total_points', 'problems_solved', 'avg_score', 'streak_days', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['updated_at']
    ordering = ['rank']
    
    actions = ['recalculate_stats']
    
    def recalculate_stats(self, request, queryset):
        for entry in queryset:
            entry.update_stats()
        self.message_user(request, f"Recalculated stats for {queryset.count()} entries")
    recalculate_stats.short_description = "Recalculate stats for selected entries"


@admin.register(LeaderboardEvent)
class LeaderboardEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'points_delta', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']