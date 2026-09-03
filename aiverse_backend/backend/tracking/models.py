from django.db import models
from django.conf import settings
import uuid


class LearnerEvent(models.Model):
    EVENT_TYPES = [
        # Content events
        ('VIDEO_STARTED', 'Video Started'),
        ('VIDEO_COMPLETED', 'Video Completed'),
        ('VIDEO_SKIPPED', 'Video Skipped'),
        ('VIDEO_REWATCHED', 'Video Rewatched'),
        ('LESSON_OPENED', 'Lesson Opened'),
        ('LESSON_COMPLETED', 'Lesson Completed'),
        # Quiz events
        ('QUIZ_STARTED', 'Quiz Started'),
        ('QUIZ_SUBMITTED', 'Quiz Submitted'),
        ('QUIZ_PASSED', 'Quiz Passed'),
        ('QUIZ_FAILED', 'Quiz Failed'),
        # Coding events
        ('CODE_SUBMITTED', 'Code Submitted'),
        ('CODE_PASSED', 'Code Passed'),
        ('CODE_FAILED', 'Code Failed'),
        ('CODE_ERROR', 'Code Error'),
        # Mentor events
        ('MENTOR_QUERIED', 'Mentor Queried'),
        # Session events
        ('SESSION_STARTED', 'Session Started'),
        ('SESSION_ENDED', 'Session Ended'),
        # Playground events
        ('PLAYGROUND_RUN', 'Playground Run'),
        # Problem events
        ('PROBLEM_OPENED', 'Problem Opened'),
        ('PROBLEM_SOLVED', 'Problem Solved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES, db_index=True)

    # Polymorphic content reference
    content_type = models.CharField(
        max_length=30,
        choices=[('lesson','lesson'),('quiz','quiz'),('problem','problem'),
                 ('video','video'),('playground','playground'),('mentor','mentor')],
        null=True, blank=True
    )
    content_id = models.IntegerField(null=True, blank=True, db_index=True)

    # Flexible metadata: score, time_spent_seconds, attempt_number, error_type, query_text etc.
    metadata = models.JSONField(default=dict)

    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['user', 'content_type', 'content_id']),
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} | {self.event_type} | {self.timestamp}"
