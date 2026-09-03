"""
Notifications & Achievements Admin Configuration

Django admin configuration for notifications and achievements.
"""

from django.contrib import admin
from .models import Notification, Achievement, UserAchievement, Milestone, UserMilestone, NotificationTemplate

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin configuration for Notification model."""
    list_display = ['user', 'notification_type', 'channel', 'is_read', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'channel', 'is_read', 'is_sent', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at', 'sent_at']
    date_hierarchy = 'created_at'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Admin configuration for Achievement model."""
    list_display = ['name', 'achievement_type', 'points', 'is_active', 'created_at']
    list_filter = ['achievement_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Admin configuration for UserAchievement model."""
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['achievement__achievement_type', 'earned_at']
    search_fields = ['user__username', 'achievement__name']
    date_hierarchy = 'earned_at'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    """Admin configuration for Milestone model."""
    list_display = ['name', 'milestone_type', 'current_value', 'target_value', 'is_completed', 'completed_at']
    list_filter = ['milestone_type', 'is_completed']
    search_fields = ['name', 'description']
    readonly_fields = ['completed_at']


@admin.register(UserMilestone)
class UserMilestoneAdmin(admin.ModelAdmin):
    """Admin configuration for UserMilestone model."""
    list_display = ['user', 'milestone', 'earned_at']
    list_filter = ['milestone__milestone_type', 'earned_at']
    search_fields = ['user__username', 'milestone__name']
    date_hierarchy = 'earned_at'


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin configuration for NotificationTemplate model."""
    list_display = ['notification_type', 'channel', 'is_active', 'created_at']
    list_filter = ['notification_type', 'channel', 'is_active']
    search_fields = ['title_template', 'message_template']