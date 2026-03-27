"""
Leaderboard management service.
Updates and maintains ranking for ML problems.
"""

from django.db.models import Q, Max
from django.contrib.auth.models import User
from .models_ml import Problem, Submission, Leaderboard


def get_leaderboard(problem: Problem, limit: int = 100) -> list:
    """
    Get leaderboard for a problem.
    
    Returns entries sorted by score (descending) with proper ranking.
    """
    entries = Leaderboard.objects.filter(problem=problem).order_by('-best_score')
    
    # Re-rank (in case of gaps)
    ranked_entries = []
    for idx, entry in enumerate(entries[:limit], 1):
        entry.rank = idx
        entry.save(update_fields=['rank'])
        ranked_entries.append(entry)
    
    return ranked_entries


def update_leaderboard_entry(
    user: User,
    problem: Problem,
    submission: 'Submission'
) -> 'Leaderboard':
    """
    Update or create leaderboard entry.
    
    Called when a submission is accepted.
    Updates best score and rank.
    """
    
    # Get or create entry
    entry, created = Leaderboard.objects.get_or_create(
        user=user,
        problem=problem,
        defaults={
            'metric': submission.metric,
            'best_score': submission.public_score,
            'best_submission': submission,
            'rank': 0,
            'total_submissions': 1,
            'total_attempts': 1,
        }
    )
    
    if not created:
        # Update if new score is better
        if submission.public_score > entry.best_score:
            entry.best_score = submission.public_score
            entry.best_submission = submission
            entry.metric = submission.metric
        
        entry.total_submissions += 1
        entry.save()
    
    # Re-rank the leaderboard
    rerank_leaderboard(problem)
    
    # Refresh from DB to get updated rank
    entry.refresh_from_db()
    
    return entry


def rerank_leaderboard(problem: Problem):
    """Re-rank all entries for a problem."""
    entries = Leaderboard.objects.filter(problem=problem).order_by('-best_score')
    
    for rank, entry in enumerate(entries, 1):
        entry.rank = rank
        entry.save(update_fields=['rank'])


def is_best_submission(submission: Submission) -> bool:
    """
    Check if this submission is the user's best on this problem.
    """
    best = Submission.objects.filter(
        user=submission.user,
        problem=submission.problem,
        status__in=['passed', 'evaluated']
    ).order_by('-public_score').first()
    
    return submission.id == best.id if best else False


def mark_best_submission(user: User, problem: Problem, submission: Submission):
    """Mark submission as best and update leaderboard."""
    
    # Mark all previous as not best
    Submission.objects.filter(
        user=user,
        problem=problem
    ).update(is_best=False)
    
    # Mark this as best
    submission.is_best = True
    submission.save(update_fields=['is_best'])


def get_user_rank(user: User, problem: Problem) -> int:
    """Get user's current rank on a problem."""
    entry = Leaderboard.objects.filter(
        user=user,
        problem=problem
    ).first()
    
    return entry.rank if entry else None


def get_leaderboard_position(user: User, problem: Problem) -> dict:
    """Get detailed position info for a user."""
    entry = Leaderboard.objects.filter(
        user=user,
        problem=problem
    ).first()
    
    if not entry:
        return None
    
    total_users = Leaderboard.objects.filter(problem=problem).count()
    
    return {
        "rank": entry.rank,
        "total_users": total_users,
        "percentile": round((entry.rank / total_users) * 100, 1) if total_users > 0 else 0,
        "best_score": entry.best_score,
        "metric": entry.metric,
        "total_submissions": entry.total_submissions,
    }
