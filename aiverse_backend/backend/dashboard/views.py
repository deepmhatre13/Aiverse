from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count, Q, Avg, Max, Min, Sum, Value, FloatField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict

from .models import UserActivity
from .serializers import (
    UserActivitySerializer,
    DashboardOverviewSerializer,
    SubmissionHistorySerializer,
    PerformanceResponseSerializer,
)
from ml.models import Submission, Problem
from mentor.models import MentorSession
from learn.models import Enrollment, LessonProgress


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """
    Get comprehensive dashboard overview with ALL metrics computed from database.
    
    Source of truth: Submission, Enrollment, LessonProgress, MentorSession tables.
    NO hardcoded values, NO frontend calculations.
    """
    user = request.user
    
    # ========== SUBMISSION STATISTICS ==========
    
    user_submissions = Submission.objects.filter(user=user)
    
    # Problems solved = distinct problems with ≥1 ACCEPTED submission
    problems_solved = user_submissions.filter(
        status='accepted'
    ).values('problem').distinct().count()
    
    # Total submissions
    total_submissions = user_submissions.count()
    
    # Accepted submissions
    accepted_submissions = user_submissions.filter(status='accepted').count()
    
    # ========== STREAK CALCULATION ==========
    
    # Get all submission dates (distinct days) - optimized query
    submission_dates = user_submissions.filter(
        created_at__isnull=False
    ).extra(
        select={'date': "DATE(created_at)"}
    ).values_list('date', flat=True).distinct()
    
    submission_days = set(submission_dates)
    
    # Calculate current streak (consecutive days with ≥1 submission, ending today)
    today = timezone.now().date()
    current_streak = 0
    check_date = today
    
    while check_date in submission_days:
        current_streak += 1
        check_date -= timedelta(days=1)
    
    # Calculate best streak (longest consecutive sequence)
    if submission_days:
        sorted_days = sorted(submission_days)
        best_streak = 1
        current_sequence = 1
        
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i-1]).days == 1:
                current_sequence += 1
                best_streak = max(best_streak, current_sequence)
            else:
                current_sequence = 1
    else:
        best_streak = 0
    
    # ========== LEARNING PERFORMANCE (Monthly avg score of ACCEPTED submissions) ==========
    
    accepted = user_submissions.filter(status='accepted')
    
    # Group by month and calculate average score
    learning_performance = []
    if accepted.exists():
        # Get all accepted submissions with dates
        monthly_scores = defaultdict(list)
        for sub in accepted.select_related('problem'):
            if sub.created_at:
                month_key = sub.created_at.strftime('%Y-%m')
                monthly_scores[month_key].append(sub.score)
        
        # Calculate averages and sort by month
        for month in sorted(monthly_scores.keys()):
            avg_score = sum(monthly_scores[month]) / len(monthly_scores[month])
            learning_performance.append({
                'month': month,
                'avg_score': round(avg_score, 4)
            })
    
    # ========== ACTIVITY HEATMAP (Count of submissions per day) ==========
    
    activity_heatmap = {}
    if user_submissions.exists():
        # Count submissions per day
        daily_counts = user_submissions.extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(count=Count('id'))
        
        for entry in daily_counts:
            if entry['date']:
                date_str = entry['date'].strftime('%Y-%m-%d')
                activity_heatmap[date_str] = entry['count']
    
    # ========== RECENT ACTIVITY ==========
    
    recent_activity = []
    
    # Add recent submissions
    recent_submissions = user_submissions.select_related('problem').order_by('-created_at')[:10]
    for sub in recent_submissions:
        recent_activity.append({
            'type': 'submission',
            'problem_title': sub.problem.title,
            'problem_slug': sub.problem.slug,
            'score': float(sub.score),
            'status': sub.status,
            'created_at': sub.created_at.isoformat() if sub.created_at else None
        })
    
    # Add recent lesson completions
    recent_lessons = LessonProgress.objects.filter(
        user=user,
        is_completed=True
    ).select_related('lesson', 'lesson__course').order_by('-last_watched_at')[:10]
    
    for progress in recent_lessons:
        recent_activity.append({
            'type': 'lesson',
            'title': progress.lesson.title,
            'course_title': progress.lesson.course.title,
            'created_at': progress.last_watched_at.isoformat() if progress.last_watched_at else None
        })
    
    # Sort by created_at descending and limit to 20 most recent
    recent_activity.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    recent_activity = recent_activity[:20]
    
    # ========== COURSES ENROLLED ==========
    
    courses_enrolled = Enrollment.objects.filter(
        user=user,
        status='active'
    ).count()
    
    # ========== MENTOR SESSIONS ==========
    
    mentor_sessions = MentorSession.objects.filter(user=user).count()
    
    # ========== BUILD RESPONSE ==========
    
    data = {
        'problems_solved': problems_solved,
        'total_submissions': total_submissions,
        'accepted_submissions': accepted_submissions,
        'current_streak': current_streak,
        'best_streak': best_streak,
        'learning_performance': learning_performance,
        'activity_heatmap': activity_heatmap,
        'recent_activity': recent_activity,
        'courses_enrolled': courses_enrolled,
        'mentor_sessions': mentor_sessions,
    }
    
    return Response(data, status=status.HTTP_200_OK)


class TimelineView(generics.ListAPIView):
    """
    Get paginated activity timeline for user
    """
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(
            user=self.request.user
        ).select_related('user', 'content_type')


class SubmissionHistoryView(generics.ListAPIView):
    """
    Get user's submission history
    """
    serializer_class = SubmissionHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Submission.objects.filter(
            user=self.request.user
        ).select_related('problem', 'user').order_by('-created_at')


class PerformanceView(APIView):
    """Authoritative performance endpoint backed only by submission aggregates."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_submissions = Submission.objects.filter(user=user).select_related('problem')
        accepted_submissions = user_submissions.filter(status='ACCEPTED')

        total_submissions = user_submissions.count()
        accepted_count = accepted_submissions.count()

        problems_solved = accepted_submissions.values('problem_id').distinct().count()
        total_score = float(
            accepted_submissions.aggregate(
                total=Coalesce(Sum('score'), Value(0.0), output_field=FloatField())
            )['total']
        )

        success_rate = round((accepted_count / total_submissions) * 100, 2) if total_submissions else 0.0

        accepted_days = set(
            day
            for day in accepted_submissions.annotate(day=TruncDate('created_at')).values_list('day', flat=True).distinct()
            if day is not None
        )
        today = timezone.localdate()
        current_streak = 0
        check_day = today
        while check_day in accepted_days:
            current_streak += 1
            check_day -= timedelta(days=1)

        global_rank = None
        if total_score > 0:
            higher_scores = (
                Submission.objects.filter(status='ACCEPTED')
                .values('user_id')
                .annotate(total=Coalesce(Sum('score'), Value(0.0), output_field=FloatField()))
                .filter(total__gt=total_score)
                .count()
            )
            global_rank = higher_scores + 1

        recent_submissions = []
        for sub in user_submissions.order_by('-created_at')[:20]:
            recent_submissions.append(
                {
                    'id': str(sub.id),
                    'problem_name': getattr(sub.problem, 'title', 'Unknown Problem'),
                    'problem_slug': getattr(sub.problem, 'slug', None),
                    'status': 'ACCEPTED' if sub.status == 'ACCEPTED' else 'FAILED',
                    'status_raw': sub.status,
                    'score': float(sub.score or 0),
                    'created_at': sub.created_at,
                }
            )

        # Lightweight analytics used by the current frontend charts
        cumulative = 0.0
        score_progression = []
        for row in (
            accepted_submissions
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(day_score=Coalesce(Sum('score'), Value(0.0), output_field=FloatField()))
            .order_by('day')
        ):
            if row['day'] is None:
                continue
            cumulative += float(row['day_score'] or 0.0)
            score_progression.append(
                {
                    'date': row['day'].isoformat(),
                    'cumulative_score': round(cumulative, 4),
                    'daily_score': round(float(row['day_score'] or 0.0), 4),
                }
            )

        difficulty_breakdown = []
        for row in (
            user_submissions.values('problem__difficulty')
            .annotate(
                total=Count('problem_id', distinct=True),
                solved=Count('problem_id', filter=Q(status='ACCEPTED'), distinct=True),
            )
            .order_by('problem__difficulty')
        ):
            difficulty_breakdown.append(
                {
                    'difficulty': row['problem__difficulty'] or 'unknown',
                    'total': row['total'],
                    'solved': row['solved'],
                }
            )

        language_distribution = []
        for row in user_submissions.values('metric').annotate(count=Count('id')).order_by('-count')[:5]:
            language_distribution.append(
                {
                    'language': row['metric'] or 'unknown',
                    'count': row['count'],
                }
            )

        activity_heatmap = []
        for row in (
            user_submissions
            .filter(created_at__gte=timezone.now() - timedelta(days=84))
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        ):
            if row['day'] is None:
                continue
            activity_heatmap.append({'date': row['day'].isoformat(), 'count': row['count']})

        payload = {
            'total_score': round(total_score, 4),
            'problems_solved': problems_solved,
            'submissions': total_submissions,
            'success_rate': success_rate,
            'current_streak': current_streak,
            'global_rank': global_rank,
            'recent_submissions': recent_submissions,
            'score_progression': score_progression,
            'difficulty_breakdown': difficulty_breakdown,
            'language_distribution': language_distribution,
            'activity_heatmap': activity_heatmap,
        }

        # Validate the required contract while allowing additional analytics keys.
        PerformanceResponseSerializer(
            data={
                'total_score': payload['total_score'],
                'problems_solved': payload['problems_solved'],
                'submissions': payload['submissions'],
                'success_rate': payload['success_rate'],
                'current_streak': payload['current_streak'],
                'global_rank': payload['global_rank'],
                'recent_submissions': [
                    {
                        'id': row['id'],
                        'problem_name': row['problem_name'],
                        'status': row['status'],
                        'score': row['score'],
                        'created_at': row['created_at'],
                    }
                    for row in payload['recent_submissions']
                ],
            }
        ).is_valid(raise_exception=True)

        return Response(payload, status=status.HTTP_200_OK)


# =====================================================================
# LIVE PERFORMANCE CENTER API
# =====================================================================

import logging

logger = logging.getLogger(__name__)

# Safe fallback response shape when metrics computation fails
LIVE_METRICS_FALLBACK = {
    "summary": {
        "active_problem": None,
        "latest_submission": None,
        "best_score": None,
        "best_metric": None,
        "rank": None,
        "total_score": 0,
        "problems_solved": 0,
        "total_submissions": 0,
        "accepted_count": 0,
        "failed_count": 0,
        "success_rate": 0.0,
        "current_streak": 0,
    },
    "activity_feed": [],
    "analytics": {
        "score_progression": [],
        "submissions_per_problem": [],
        "status_distribution": [],
        "activity_heatmap": [],
        "problems_by_difficulty": [],
        # These keys are referenced by the frontend chart component.
        "difficulty_breakdown": [],
        "language_distribution": [],
    },
    "server_time": None,
}


class LiveMetricsView(APIView):
    """
    GET /api/dashboard/live-metrics/
    
    Unified endpoint for Live Performance Center.
    Combines Timeline + Dashboard data for real-time updates.
    
    Returns:
    - summary: Live metrics summary (rank, score, submissions)
    - activity_feed: Chronological feed of recent events
    - analytics: Performance charts data
    
    Defensive: Always returns 200 with safe fallback on any error.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Guard: Never assume request.user is valid
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return Response(LIVE_METRICS_FALLBACK, status=status.HTTP_401_UNAUTHORIZED)
        
        now = timezone.now()
        
        try:
            return self._compute_metrics(request, user, now)
        except Exception as exc:
            logger.exception("LiveMetricsView failed: %s", exc)
            fallback = {**LIVE_METRICS_FALLBACK, "server_time": now.isoformat()}
            return Response(fallback, status=status.HTTP_200_OK)
    
    def _compute_metrics(self, request, user, now):
        """Compute live metrics with guarded aggregations."""
        # ========== LIVE SUMMARY PANEL ==========
        
        user_submissions = Submission.objects.filter(user=user)
        latest_submission = user_submissions.order_by('-created_at').first()
        accepted_submissions = user_submissions.filter(status='accepted')
        best_submission = accepted_submissions.order_by('-score').first()
        
        active_problem = None
        if latest_submission and hasattr(latest_submission, 'problem') and latest_submission.problem:
            active_problem = {
                'id': latest_submission.problem.id,
                'title': getattr(latest_submission.problem, 'title', ''),
                'slug': getattr(latest_submission.problem, 'slug', ''),
                'metric': getattr(latest_submission, 'metric', None),
            }
        
        total_submissions = user_submissions.count() or 0
        accepted_count = accepted_submissions.count() or 0
        failed_count = max(total_submissions - accepted_count, 0)

        # Rank: prefer the persisted global_rank if available; fall back to Redis.
        rank = getattr(user, 'global_rank', None)
        if rank in (0,):  # treat 0 as unranked
            rank = None
        if rank is None and accepted_submissions.exists():
            try:
                from utils.leaderboard import get_rank
                rank = get_rank('alltime', str(user.pk))
            except Exception:
                rank = None
        
        submission_days = set()
        try:
            submission_dates = user_submissions.filter(
                created_at__isnull=False
            ).extra(
                select={'date': "DATE(created_at)"}
            ).values_list('date', flat=True).distinct()
            submission_days = set(submission_dates or [])
        except Exception:
            pass
        
        today = now.date()
        current_streak = 0
        check_date = today
        while check_date in submission_days:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # Distinct problems with at least one accepted submission.
        problems_solved = accepted_submissions.values('problem').distinct().count()

        # Total score is sourced from accepted submissions to avoid cache drift.
        total_score = accepted_submissions.aggregate(total=Sum('score')).get('total') or 0
        total_score = int(total_score)

        success_rate = round((accepted_count / total_submissions) * 100, 2) if total_submissions > 0 else 0.0

        # Streak should come from the persisted user field when available.
        persisted_streak = getattr(user, 'streak_days', None)
        current_streak = int(persisted_streak or current_streak)

        summary = {
            'active_problem': active_problem,
            'latest_submission': {
                'id': latest_submission.id,
                'status': latest_submission.status,
                'score': float(latest_submission.score) if latest_submission and latest_submission.score is not None else None,
                'metric': getattr(latest_submission, 'metric', None),
                'execution_time': float(latest_submission.runtime_seconds) if latest_submission and getattr(latest_submission, 'runtime_seconds', None) is not None else None,
                'timestamp': latest_submission.created_at.isoformat() if latest_submission and latest_submission.created_at else None,
            } if latest_submission else None,
            'best_score': float(best_submission.score) if best_submission and best_submission.score is not None else None,
            'best_metric': getattr(best_submission, 'metric', None) if best_submission else None,
            'rank': rank,
            'total_score': total_score,
            'problems_solved': problems_solved,
            'total_submissions': total_submissions,
            'accepted_count': accepted_count,
            'failed_count': failed_count,
            'success_rate': success_rate,
            'current_streak': current_streak,
        }
        
        # ========== LIVE ACTIVITY FEED ==========
        
        activity_feed = []
        
        try:
            recent_submissions = list(user_submissions.select_related('problem').order_by('-created_at')[:50])
        except Exception:
            recent_submissions = []
        
        for sub in recent_submissions:
            problem = getattr(sub, 'problem', None)
            if not problem:
                continue
            try:
                prev_sub = user_submissions.filter(
                    problem=problem,
                    created_at__lt=sub.created_at
                ).order_by('-created_at').first()
                
                score_delta = None
                if prev_sub and prev_sub.score is not None and sub.score is not None:
                    score_delta = float(sub.score) - float(prev_sub.score)
                
                activity_feed.append({
                    'id': f'sub_{sub.id}',
                    'type': 'submission',
                    'event': 'evaluation_completed',
                    'problem': {
                        'id': problem.id,
                        'title': getattr(problem, 'title', ''),
                        'slug': getattr(problem, 'slug', ''),
                    },
                    'problem_id': problem.id,
                    'problem_title': getattr(problem, 'title', ''),
                    'problem_slug': getattr(problem, 'slug', ''),
                    'submitted_at': sub.created_at.isoformat() if sub.created_at else None,
                    'status': getattr(sub, 'status', None),
                    'score': float(sub.score) if sub.score is not None else None,
                    'score_delta': round(score_delta, 4) if score_delta is not None else None,
                    'language': getattr(sub, 'language', None),
                    'metric': getattr(sub, 'metric', None),
                    'execution_time': float(sub.runtime_seconds) if getattr(sub, 'runtime_seconds', None) is not None else None,
                    'timestamp': sub.created_at.isoformat() if sub.created_at else None,
                })
            except Exception:
                continue
        
        try:
            recent_lessons = list(LessonProgress.objects.filter(
                user=user,
                is_completed=True
            ).select_related('lesson', 'lesson__course').order_by('-last_watched_at')[:20])
        except Exception:
            recent_lessons = []
        
        for progress in recent_lessons:
            lesson = getattr(progress, 'lesson', None)
            course = getattr(lesson, 'course', None) if lesson else None
            ts = getattr(progress, 'completed_at', None) or getattr(progress, 'last_watched_at', None)
            activity_feed.append({
                'id': f'lesson_{progress.id}',
                'type': 'lesson',
                'event': 'lesson_completed',
                'lesson': {
                    'id': lesson.id if lesson else None,
                    'title': getattr(lesson, 'title', '') if lesson else '',
                    'course_title': getattr(course, 'title', '') if course else '',
                },
                'timestamp': ts.isoformat() if ts else None,
            })
        
        # Sort by timestamp descending
        activity_feed.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        activity_feed = activity_feed[:50]  # Limit to 50 items
        
        # ========== PERFORMANCE ANALYTICS ==========
        
        analytics = {
            'score_progression': [],
            'submissions_per_problem': [],
            'status_distribution': [],
            'activity_heatmap': [],
            'problems_by_difficulty': [],
        }
        
        try:
            score_progression = []
            if accepted_submissions.exists():
                daily_scores = defaultdict(list)
                for sub in accepted_submissions.order_by('created_at'):
                    if sub.created_at and sub.score is not None:
                        date_key = sub.created_at.strftime('%Y-%m-%d')
                        daily_scores[date_key].append(float(sub.score))
                
                for date in sorted(daily_scores.keys()):
                    vals = daily_scores[date]
                    n = len(vals)
                    avg_score = sum(vals) / n if n > 0 else 0
                    best_score = max(vals) if vals else 0
                    score_progression.append({
                        'date': date,
                        'avg_score': round(avg_score, 4),
                        'best_score': round(best_score, 4),
                        'count': n,
                    })
            analytics['score_progression'] = score_progression
        except Exception:
            pass
        
        try:
            analytics['submissions_per_problem'] = list(
                user_submissions.values('problem__title', 'problem__slug')
                .annotate(
                    total=Count('id'),
                    accepted=Count('id', filter=Q(status='accepted')),
                    failed=Count(
                        'id',
                        filter=Q(status__in=['wrong_answer', 'runtime_error', 'time_limit_exceeded', 'compilation_error']),
                    ),
                )
                .order_by('-total')[:10]
            )
        except Exception:
            pass
        
        try:
            analytics['status_distribution'] = list(
                user_submissions.values('status')
                .annotate(count=Count('id'))
            )
        except Exception:
            pass
        
        try:
            activity_heatmap = []
            cutoff = now - timedelta(days=30)
            for sub in user_submissions.filter(created_at__gte=cutoff):
                if sub.created_at:
                    day = sub.created_at.strftime('%a')
                    hour = sub.created_at.hour
                    activity_heatmap.append({'day': day, 'hour': hour})
            
            heatmap_counts = defaultdict(int)
            for item in activity_heatmap:
                key = f"{item['day']}_{item['hour']}"
                heatmap_counts[key] += 1
            
            analytics['activity_heatmap'] = [
                {'day': k.split('_')[0], 'hour': int(k.split('_')[1]), 'count': v}
                for k, v in heatmap_counts.items()
            ]
        except Exception:
            pass
        
        try:
            analytics['problems_by_difficulty'] = list(
                user_submissions.filter(status='accepted')
                .values('problem__difficulty')
                .annotate(count=Count('problem', distinct=True))
            )
        except Exception:
            pass
        
        return Response({
            'summary': summary,
            'activity_feed': activity_feed,
            'analytics': analytics,
            'server_time': now.isoformat(),
        }, status=status.HTTP_200_OK)