import uuid
from django.db import models
from django.conf import settings


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('runtime_error', 'Runtime Error'),
        ('time_limit_exceeded', 'Time Limit Exceeded'),
        ('compilation_error', 'Compilation Error'),
    ]
    LANGUAGE_CHOICES = [
        ('python', 'Python'), ('r', 'R'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aiverse_submissions'
    )
    problem = models.ForeignKey(
        'problems.Problem', on_delete=models.CASCADE, related_name='submissions'
    )
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    score = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    max_score = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    memory_mb = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    test_results = models.JSONField(default=list)
    error_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_best = models.BooleanField(default=False)

    class Meta:
        db_table = 'submissions'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['problem']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'problem']),
            models.Index(fields=['-submitted_at']),
        ]

    def __str__(self):
        return f'{self.user} → {self.problem.slug} [{self.status}]'
