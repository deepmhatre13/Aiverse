from django.contrib import admin
from .models import ActivityEvent, PerformanceSnapshot


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'reference_id', 'score_delta', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PerformanceSnapshot)
class PerformanceSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'problems_attempted', 'problems_solved', 'avg_score', 'streak_day']
    list_filter = ['date']
    search_fields = ['user__email', 'user__username']
    ordering = ['-date']
    date_hierarchy = 'date'
    
    actions = ['regenerate_snapshots']
    
    def regenerate_snapshots(self, request, queryset):
        for snapshot in queryset:
            PerformanceSnapshot.generate_for_date(snapshot.user, snapshot.date)
        self.message_user(request, f"Regenerated {queryset.count()} snapshots")
    regenerate_snapshots.short_description = "Regenerate selected snapshots"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')