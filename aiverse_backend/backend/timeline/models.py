from django.db import models
from django.conf import settings


class ActivityEvent(models.Model):
    EVENT_TYPES = [
        ('submission', 'Submission'),
        ('submission_success', 'Submission Success'),
        ('submission_fail', 'Submission Failed'),
        ('video_completed', 'Video Completed'),
        ('mentor_used', 'Mentor Used'),
        ('problem_solved', 'Problem Solved'),
        ('course_purchased', 'Course Purchased'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, db_index=True)
    reference_id = models.IntegerField(null=True, blank=True)
    score_delta = models.FloatField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'event_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_event_type_display()} at {self.created_at}"


class PerformanceSnapshot(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_snapshots'
    )
    date = models.DateField(db_index=True)
    problems_attempted = models.IntegerField(default=0)
    problems_solved = models.IntegerField(default=0)
    avg_score = models.FloatField(default=0.0)
    streak_day = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.date}"

    @classmethod
    def generate_for_date(cls, user, date):
        """Generate or update snapshot for a specific date"""
        from ml.models import Submission
        from django.db.models import Avg, Count
        
        # Get submissions for this date
        submissions_today = Submission.objects.filter(
            user=user,
            submitted_at__date=date
        )
        
        problems_attempted = submissions_today.values('problem').distinct().count()
        
        problems_solved = submissions_today.filter(
            status='completed',
            score__gte=70
        ).values('problem').distinct().count()
        
        avg_score_today = submissions_today.filter(
            status='completed'
        ).aggregate(avg=Avg('score'))['avg'] or 0.0
        
        # Get streak (from leaderboard if available)
        try:
            from leaderboard.models import LeaderboardEntry
            entry = LeaderboardEntry.objects.get(user=user)
            streak_day = entry.streak_days
        except:
            streak_day = 0
        
        snapshot, created = cls.objects.update_or_create(
            user=user,
            date=date,
            defaults={
                'problems_attempted': problems_attempted,
                'problems_solved': problems_solved,
                'avg_score': round(avg_score_today, 2),
                'streak_day': streak_day
            }
        )
        
        return snapshot