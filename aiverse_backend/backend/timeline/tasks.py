from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import PerformanceSnapshot

User = get_user_model()


@shared_task
def generate_daily_snapshots():
    """
    Celery task to generate performance snapshots for all users
    Run this daily via Celery Beat
    """
    today = timezone.now().date()
    users = User.objects.filter(is_active=True)
    
    count = 0
    for user in users:
        # Only generate if user had activity today
        from .models import ActivityEvent
        has_activity = ActivityEvent.objects.filter(
            user=user,
            created_at__date=today
        ).exists()
        
        if has_activity:
            PerformanceSnapshot.generate_for_date(user, today)
            count += 1
    
    return f"Generated {count} snapshots for {today}"


@shared_task
def backfill_snapshots(user_id, start_date, end_date):
    """
    Backfill snapshots for a user over a date range
    """
    from datetime import timedelta
    
    user = User.objects.get(id=user_id)
    current = start_date
    count = 0
    
    while current <= end_date:
        PerformanceSnapshot.generate_for_date(user, current)
        count += 1
        current += timedelta(days=1)
    
    return f"Backfilled {count} snapshots for user {user.email}"