from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('problem_attempted', 'Problem Attempted'),
        ('submission_success', 'Submission Success'),
        ('submission_failed', 'Submission Failed'),
        ('video_watched', 'Video Watched'),
        ('course_purchased', 'Course Purchased'),
        ('mentor_question', 'Mentor Question'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES, db_index=True)
    
    # Generic relation to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User Activities'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'activity_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} at {self.created_at}"