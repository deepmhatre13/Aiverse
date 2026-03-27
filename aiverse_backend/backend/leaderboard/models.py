from django.db import models
from django.conf import settings
from django.utils import timezone


class LeaderboardEntry(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entry'
    )
    total_points = models.IntegerField(default=0, db_index=True)
    problems_solved = models.IntegerField(default=0)
    avg_score = models.FloatField(default=0.0)
    streak_days = models.IntegerField(default=0)
    rank = models.IntegerField(default=0, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_points', 'updated_at']
        indexes = [
            models.Index(fields=['-total_points', 'updated_at']),
            models.Index(fields=['user', '-total_points']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.total_points} points (Rank #{self.rank})"

    def calculate_points(self):
        """
        Calculate total points based on:
        - Problems solved: 100 points each
        - Average score percentile: 0-50 bonus points
        - Streak bonus: 10 points per streak day
        - Penalty for low success rate
        """
        from ml.models import Submission
        
        # Base points from problems solved
        points = self.problems_solved * 100
        
        # Bonus for high average score
        if self.avg_score >= 90:
            points += 50
        elif self.avg_score >= 80:
            points += 30
        elif self.avg_score >= 70:
            points += 15
        
        # Streak bonus
        points += self.streak_days * 10
        
        # Penalty for excessive failures
        total_submissions = Submission.objects.filter(user=self.user).count()
        if total_submissions > 0:
            success_rate = (self.problems_solved / total_submissions) * 100
            if success_rate < 30:
                points = int(points * 0.8)  # 20% penalty
            elif success_rate < 50:
                points = int(points * 0.9)  # 10% penalty
        
        return points

    def update_stats(self):
        """Update all stats and recalculate points"""
        from ml.models import Submission
        from django.db.models import Avg, Count
        
        # Count unique problems solved (score >= 70)
        solved = Submission.objects.filter(
            user=self.user,
            status='completed',
            score__gte=70
        ).values('problem').distinct().count()
        
        # Calculate average score from completed submissions
        avg = Submission.objects.filter(
            user=self.user,
            status='completed'
        ).aggregate(avg_score=Avg('score'))
        
        self.problems_solved = solved
        self.avg_score = avg['avg_score'] or 0.0
        self.total_points = self.calculate_points()
        self.save()


class LeaderboardEvent(models.Model):
    EVENT_TYPES = [
        ('submission_success', 'Submission Success'),
        ('submission_fail', 'Submission Failed'),
        ('streak_bonus', 'Streak Bonus'),
        ('problem_solved', 'Problem Solved'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_events'
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    points_delta = models.IntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.event_type} ({self.points_delta:+d})"


class LeaderboardSnapshot(models.Model):
    PERIOD_CHOICES = [
        ('alltime', 'All Time'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_snapshots'
    )
    rank = models.IntegerField()
    score = models.IntegerField(default=0)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, db_index=True)
    snapshot_date = models.DateField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_date', 'rank']
        unique_together = ('user', 'period', 'snapshot_date')
        indexes = [
            models.Index(fields=['period', 'snapshot_date', 'rank']),
            models.Index(fields=['user', 'period', 'snapshot_date']),
        ]

    def __str__(self):
        return f"{self.user_id} [{self.period}] #{self.rank} @ {self.snapshot_date}"