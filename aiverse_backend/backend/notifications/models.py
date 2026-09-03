"""
Notifications & Achievements Models

Django models for notifications and achievements system.
"""

from django.db import models
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Notification(models.Model):
    """Notification model for user notifications."""
    
    NOTIFICATION_TYPES = (
        ('struggling_state_change', 'Struggling State Change'),
        ('revision_due', 'Revision Due'),
        ('streak_risk', 'Streak Risk'),
        ('mastery_achieved', 'Mastery Achieved'),
        ('weak_topic_improvement', 'Weak Topic Improvement'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('mentor_session_scheduled', 'Mentor Session Scheduled'),
        ('easy_win_recommended', 'Easy Win Recommended'),
    )
    
    CHANNELS = (
        ('push', 'Push Notification'),
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('sms', 'SMS'),
    )
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=CHANNELS, default='in_app')
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Additional metadata
    
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['scheduled_for', 'is_sent']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type}"
    
    def mark_as_sent(self):
        """Mark notification as sent."""
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save()


class Achievement(models.Model):
    """Achievement model for gamification."""
    
    ACHIEVEMENT_TYPES = (
        ('concept_mastery', 'Concept Mastery'),
        ('streak', 'Streak'),
        ('improvement', 'Improvement'),
        ('experiment', 'Experiment'),
        ('milestone', 'Milestone'),
    )
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=100, default='🏆')
    points = models.IntegerField(default=100)
    
    # Criteria
    criteria = models.JSONField(default=dict)  # e.g., {"concept_count": 5, "timeframe_days": 7}
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['points']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """User achievement record."""
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    earned_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-earned_at']
        unique_together = ['user', 'achievement']
        indexes = [
            models.Index(fields=['user', '-earned_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class Milestone(models.Model):
    """Milestone model for tracking progress."""
    
    MILESTONE_TYPES = (
        ('concept', 'Concept Mastery'),
        ('platform', 'Platform-wide'),
        ('streak', 'Streak'),
        ('improvement', 'Improvement'),
    )
    
    name = models.CharField(max_length=255)
    milestone_type = models.CharField(max_length=50, choices=MILESTONE_TYPES)
    description = models.TextField()
    
    # Target criteria
    target_value = models.IntegerField()
    current_value = models.IntegerField(default=0)
    unit = models.CharField(max_length=50, default='count')  # count, days, percentage
    
    # For concept milestones
    concept_tag = models.CharField(max_length=100, null=True, blank=True)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['target_value']
    
    def __str__(self):
        return f"{self.name} ({self.current_value}/{self.target_value})"
    
    def update_progress(self, value: int):
        """Update milestone progress."""
        self.current_value = min(value, self.target_value)
        
        if self.current_value >= self.target_value and not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            logger.info(f"Milestone completed: {self.name}")
        
        self.save()


class UserMilestone(models.Model):
    """User milestone record."""
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='milestones')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='user_milestones')
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-earned_at']
        unique_together = ['user', 'milestone']
    
    def __str__(self):
        return f"{self.user.username} - {self.milestone.name}"


class NotificationTemplate(models.Model):
    """Template for notifications."""
    
    notification_type = models.CharField(max_length=50, choices=Notification.NOTIFICATION_TYPES)
    channel = models.CharField(max_length=20, choices=Notification.CHANNELS)
    
    title_template = models.CharField(max_length=255)
    message_template = models.TextField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['notification_type', 'channel']
    
    def __str__(self):
        return f"{self.notification_type} - {self.channel}"