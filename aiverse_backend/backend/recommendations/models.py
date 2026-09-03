from django.db import models
from django.conf import settings


class Recommendation(models.Model):
    RECOMMENDATION_TYPES = [
        ('next_lesson', 'Next Lesson'),
        ('revision', 'Revision'),
        ('prerequisite', 'Prerequisite'),
        ('quiz', 'Quiz'),
        ('coding_problem', 'Coding Problem'),
        ('project', 'Project'),
    ]
    SOURCES = [
        ('rule_based', 'Rule Based'),
        ('content_based', 'Content Based'),
        ('collaborative', 'Collaborative Filtering'),
        ('ml_model', 'ML Model'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendations')
    recommendation_type = models.CharField(max_length=30, choices=RECOMMENDATION_TYPES)
    content_type = models.CharField(max_length=20)  # 'lesson', 'quiz', 'problem'
    content_id = models.IntegerField()
    score = models.FloatField(default=0.0)  # relevance score
    reason = models.CharField(max_length=255)  # human-readable explanation
    source = models.CharField(max_length=30, choices=SOURCES, default='rule_based')
    is_dismissed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-score', '-generated_at']
        indexes = [models.Index(fields=['user', 'recommendation_type', 'is_dismissed'])]
