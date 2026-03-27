from celery import shared_task
from django.utils import timezone

from .models import LeaderboardSnapshot
from utils.leaderboard import get_top


@shared_task
def snapshot_leaderboard(period: str = 'weekly', limit: int = 10000):
    """Capture a rank snapshot from Redis sorted set for delta calculations."""
    if period not in ('alltime', 'weekly', 'monthly'):
        return f"Invalid period: {period}"

    today = timezone.now().date()
    rows = get_top(period, count=limit, offset=0)

    if not rows:
        return f"No rows found for {period}; snapshot skipped"

    # Replace today's snapshot for this period to keep it idempotent.
    LeaderboardSnapshot.objects.filter(period=period, snapshot_date=today).delete()

    snapshots = []
    for idx, (user_id, score) in enumerate(rows, start=1):
        snapshots.append(
            LeaderboardSnapshot(
                user_id=user_id,
                rank=idx,
                score=int(score),
                period=period,
                snapshot_date=today,
            )
        )

    LeaderboardSnapshot.objects.bulk_create(snapshots, batch_size=1000)
    return f"Captured {len(snapshots)} {period} snapshot rows for {today}"
