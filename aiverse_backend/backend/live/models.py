import uuid
from django.db import models
from django.conf import settings


class LiveSession(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('ended', 'Ended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='hosted_sessions'
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    participant_count = models.IntegerField(default=0)
    max_participants = models.IntegerField(default=500)
    stream_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'live_sessions'
        ordering = ['starts_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['starts_at']),
        ]

    def __str__(self):
        return f'{self.title} [{self.status}]'

    @property
    def is_active(self):
        return self.status == 'live'


class LiveRegistration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='live_registrations'
    )
    session = models.ForeignKey(
        LiveSession, on_delete=models.CASCADE, related_name='registrations'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        db_table = 'live_registrations'
        unique_together = ('user', 'session')
