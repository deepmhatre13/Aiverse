from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import LeaderboardEntry, LeaderboardEvent


@receiver(post_save, sender='problems.Submission')
def update_leaderboard_on_submission(sender, instance, created, **kwargs):
    """Update leaderboard when submission is evaluated"""
    if instance.status != 'completed':
        return
    
    # Get or create leaderboard entry
    entry, _ = LeaderboardEntry.objects.get_or_create(user=instance.user)
    
    with transaction.atomic():
        # Determine event type and points
        if instance.score >= 70:
            event_type = 'submission_success'
            # Check if this is first time solving this problem
            from ml.models import Submission
            is_first_solve = not Submission.objects.filter(
                user=instance.user,
                problem=instance.problem,
                status='completed',
                score__gte=70
            ).exclude(id=instance.id).exists()
            
            if is_first_solve:
                points_delta = 100  # New problem solved
                LeaderboardEvent.objects.create(
                    user=instance.user,
                    event_type='problem_solved',
                    points_delta=points_delta,
                    metadata={
                        'problem_id': instance.problem.id,
                        'score': instance.score,
                        'submission_id': instance.id
                    }
                )
            else:
                points_delta = 0  # No points for re-solving
        else:
            event_type = 'submission_fail'
            points_delta = -5  # Small penalty
            
            LeaderboardEvent.objects.create(
                user=instance.user,
                event_type=event_type,
                points_delta=points_delta,
                metadata={
                    'problem_id': instance.problem.id,
                    'score': instance.score,
                    'submission_id': instance.id
                }
            )
        
        # Update entry stats
        entry.update_stats()
        
        # Recalculate ranks
        recalculate_ranks()


def recalculate_ranks():
    """Recalculate ranks for all leaderboard entries"""
    entries = LeaderboardEntry.objects.all().order_by('-total_points', 'updated_at')
    
    for idx, entry in enumerate(entries, start=1):
        if entry.rank != idx:
            entry.rank = idx
            entry.save(update_fields=['rank'])


@receiver(post_save, sender='dashboard.UserActivity')
def update_streak_on_activity(sender, instance, created, **kwargs):
    """Update streak when user has daily activity"""
    if not created:
        return
    
    entry, _ = LeaderboardEntry.objects.get_or_create(user=instance.user)
    
    # Check if this is a new day of activity
    from datetime import date, timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get last activity before today
    last_activity = sender.objects.filter(
        user=instance.user,
        created_at__date__lt=today
    ).order_by('-created_at').first()
    
    if last_activity:
        last_date = last_activity.created_at.date()
        if last_date == yesterday:
            # Consecutive day - increment streak
            entry.streak_days += 1
            entry.save()
            
            LeaderboardEvent.objects.create(
                user=instance.user,
                event_type='streak_bonus',
                points_delta=10,
                metadata={'streak_days': entry.streak_days}
            )
        elif last_date < yesterday:
            # Streak broken - reset to 1
            entry.streak_days = 1
            entry.save()
    else:
        # First activity ever
        entry.streak_days = 1
        entry.save()