"""
Notifications & Achievements Serializers

Django REST Framework serializers for notifications and achievements.
"""

from rest_framework import serializers
from .models import Notification, Achievement, UserAchievement, Milestone, UserMilestone
import logging

logger = logging.getLogger(__name__)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'channel', 'title', 'message',
            'data', 'is_read', 'is_sent', 'sent_at', 'created_at', 'scheduled_for'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at']


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model."""
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'name', 'slug', 'achievement_type', 'description',
            'icon', 'points', 'criteria', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for UserAchievement model."""
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = [
            'id', 'user', 'achievement', 'earned_at', 'metadata'
        ]
        read_only_fields = ['id', 'earned_at']


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for Milestone model."""
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'milestone_type', 'description',
            'target_value', 'current_value', 'unit', 'concept_tag',
            'is_completed', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at']


class UserMilestoneSerializer(serializers.ModelSerializer):
    """Serializer for UserMilestone model."""
    milestone = MilestoneSerializer(read_only=True)
    
    class Meta:
        model = UserMilestone
        fields = [
            'id', 'user', 'milestone', 'earned_at'
        ]
        read_only_fields = ['id', 'earned_at']


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer for creating notifications."""
    notification_type = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    channel = serializers.ChoiceField(choices=Notification.CHANNELS, default='in_app')
    data = serializers.DictField(required=False, default=dict)
    scheduled_for = serializers.DateTimeField(required=False, allow_null=True)


class AchievementCheckSerializer(serializers.Serializer):
    """Serializer for achievement check request."""
    user_id = serializers.IntegerField()