from django.contrib import admin
from .models import Problem, Submission


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'problem_type', 'metric', 'is_active', 'created_at']
    list_filter = ['problem_type', 'metric', 'is_active']
    search_fields = ['title', 'slug', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'description', 'is_active')
        }),
        ('Problem Configuration', {
            'fields': ('problem_type', 'metric', 'target_column', 'dataset_dir')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'problem', 'status', 'score', 'created_at']
    list_filter = ['status', 'problem', 'created_at']
    search_fields = ['user__email', 'problem__title']
    readonly_fields = ['created_at', 'code']
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('user', 'problem', 'status')
        }),
        ('Code (read-only)', {
            'fields': ('code',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('score', 'metric', 'threshold', 'rank', 'reason')
        }),
        ('Diagnostics', {
            'fields': ('error_log', 'runtime_seconds', 'test_results'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Submissions should only be created via API
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Submissions are immutable - never delete
        return False
