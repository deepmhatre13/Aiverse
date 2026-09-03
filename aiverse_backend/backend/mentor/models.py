from django.db import models
from django.conf import settings


class MentorSession(models.Model):
    """User session for mentor interactions. One per user per conversation thread."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_active_at']
        indexes = [
            models.Index(fields=['user', '-last_active_at']),
        ]

    def __str__(self):
        return f"Session {self.id} - {self.user.email}"


class MentorMessage(models.Model):
    """Message in a mentor session. Role must be strictly 'user' or 'assistant'."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(MentorSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        db_index=True,
        help_text="Must be 'user' or 'assistant' (lowercase)"
    )
    content = models.TextField(help_text="Full message text. For assistant, may contain JSON structure or plain text.")
    concept_tag = models.CharField(max_length=50, blank=True, null=True, help_text="Primary concept tag of this message")
    agent_used = models.CharField(max_length=50, blank=True, null=True, help_text="Agent that generated response")
    faithfulness_score = models.FloatField(null=True, blank=True, help_text="RAGAS faithfulness score (0.0 - 1.0)")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['session', 'role', 'created_at']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class MentorMemoryBlob(models.Model):
    """PostgreSQL durable write-through store for long-term memory blobs beyond Redis TTL."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mentor_memory_blobs')
    memory_type = models.CharField(max_length=50, db_index=True)
    payload = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'memory_type')
        indexes = [
            models.Index(fields=['user', 'memory_type']),
        ]

    def __str__(self):
        return f"MemoryBlob({self.user_id}, {self.memory_type})"