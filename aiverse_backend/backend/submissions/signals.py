"""
Django signals for the submissions app.
On Submission save with status='accepted':
  1. Atomic User stat updates via F() expressions
  2. Streak logic
  3. Redis ZADD for leaderboard ZSETs
  4. Recalculate global_rank from ZREVRANK
  5. Bust profile cache
  6. Broadcast via Django Channels
"""
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from utils.cache import cache_bust, profile_cache_key, leaderboard_hot_cache_keys

from .models import Submission


@receiver(post_save, sender=Submission)
def handle_submission_saved(sender, instance, created, **kwargs):
    if not created:
        return  # Submissions treated as immutable after creation

    user = instance.user
    problem = instance.problem

    # Always increment total_submissions
    from django.contrib.auth import get_user_model
    User = get_user_model()

    with transaction.atomic():
        if instance.status == 'accepted':
            # Check if this is user's first solve for this problem
            prev_accepted = Submission.objects.filter(
                user=user, problem=problem, status='accepted'
            ).exclude(pk=instance.pk).exists()

            score_delta = int(instance.score) if not prev_accepted else 0
            problems_solved_delta = 1 if not prev_accepted else 0

            today = timezone.now().date()

            # Fetch current streak info
            user_obj = User.objects.select_for_update().get(pk=user.pk)
            last_date = user_obj.last_submission_date

            if last_date == today - timedelta(days=1):
                new_streak = user_obj.streak_days + 1
            elif last_date == today:
                new_streak = user_obj.streak_days
            else:
                new_streak = 1

            new_longest = max(user_obj.longest_streak, new_streak)

            User.objects.filter(pk=user.pk).update(
                total_score=F('total_score') + score_delta,
                weekly_score=F('weekly_score') + score_delta,
                monthly_score=F('monthly_score') + score_delta,
                problems_solved=F('problems_solved') + problems_solved_delta,
                accepted_submissions=F('accepted_submissions') + 1,
                total_submissions=F('total_submissions') + 1,
                streak_days=new_streak,
                longest_streak=new_longest,
                last_submission_date=today,
                last_active=timezone.now(),
            )
        else:
            User.objects.filter(pk=user.pk).update(
                total_submissions=F('total_submissions') + 1,
                last_active=timezone.now(),
            )

    # Bust profile cache
    cache_bust(profile_cache_key(user.pk))

    # Update Redis leaderboard ZSETs
    if instance.status == 'accepted':
        _update_redis_leaderboard(user)
        _broadcast_submission(instance, user)


def _update_redis_leaderboard(user):
    """ZADD leaderboard ZSETs and update global_rank."""
    try:
        from utils.leaderboard import zadd_scores_atomic, get_rank
        from django.contrib.auth import get_user_model
        User = get_user_model()

        fresh = User.objects.get(pk=user.pk)
        zadd_scores_atomic(
            str(user.pk),
            fresh.total_score,
            fresh.weekly_score,
            fresh.monthly_score,
        )

        new_rank = get_rank('alltime', str(user.pk))
        if new_rank is not None:
            User.objects.filter(pk=user.pk).update(global_rank=new_rank)

        # Leaderboard list caches should refresh quickly after rank changes.
        cache_bust(*leaderboard_hot_cache_keys())
    except Exception:
        pass  # Non-blocking


def _broadcast_submission(instance, user):
    """Broadcast accepted submission to Django Channels groups."""
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from django.contrib.auth import get_user_model
        User = get_user_model()

        fresh = User.objects.get(pk=user.pk)
        channel_layer = get_channel_layer()

        activity_msg = {
            'type': 'activity_event',
            'event_type': 'submission_accepted',
            'problem_title': instance.problem.title,
            'problem_slug': instance.problem.slug,
            'points': int(instance.score),
            'new_rank': fresh.global_rank,
            'timestamp': timezone.now().isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            f'activity_{user.pk}', activity_msg
        )

        leaderboard_msg = {
            'type': 'leaderboard_update',
            'user_id': str(user.pk),
            'username': fresh.username,
            'display_name': fresh.display_name or fresh.username,
            'new_total_score': fresh.total_score,
            'new_rank': fresh.global_rank,
            'problem_title': instance.problem.title,
            'points_earned': int(instance.score),
        }
        async_to_sync(channel_layer.group_send)('leaderboard', leaderboard_msg)
    except Exception:
        pass  # Non-blocking
