from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Max, Min, Q
from collections import defaultdict

from .models import LeaderboardEntry, LeaderboardEvent, LeaderboardSnapshot
from .serializers import LeaderboardEntrySerializer, LeaderboardEventSerializer
from ml.models import Submission, Problem
from ml.metrics import LOWER_IS_BETTER_METRICS
from utils.cache import cache_get, cache_set, leaderboard_top_cache_key, CacheTTL
from utils.leaderboard import get_top, get_rank
from users.models import User
from rest_framework.views import APIView


def _normalize_period(period: str) -> str:
    raw = (period or 'all_time').strip().lower()
    mapping = {
        'all_time': 'alltime',
        'alltime': 'alltime',
        'monthly': 'monthly',
        'weekly': 'weekly',
    }
    return mapping.get(raw, 'alltime')


def _latest_snapshot_rank_map(period: str) -> dict:
    latest_date = (
        LeaderboardSnapshot.objects
        .filter(period=period)
        .aggregate(latest=Max('snapshot_date'))
        .get('latest')
    )
    if not latest_date:
        return {}

    rows = (
        LeaderboardSnapshot.objects
        .filter(period=period, snapshot_date=latest_date)
        .values_list('user_id', 'rank')
    )
    return {str(user_id): int(rank) for user_id, rank in rows}


class LeaderboardListView(APIView):
    """Redis-first leaderboard endpoint.

    GET /api/leaderboard/?period=all_time|monthly|weekly&page=1&limit=25
    """

    permission_classes = [AllowAny]

    def _hydrate_rows(self, redis_rows, offset, previous_rank_map):
        user_ids = [uid for uid, _ in redis_rows]
        users_map = {
            str(u.pk): u
            for u in User.objects.filter(pk__in=user_ids).only(
                'id', 'username', 'display_name', 'avatar_url',
                'total_score', 'weekly_score', 'monthly_score', 'problems_solved'
            )
        }

        rows = []
        for idx, (uid, score) in enumerate(redis_rows):
            user = users_map.get(str(uid))
            if not user:
                continue
            solved = int(user.problems_solved or 0)
            avg_score = round((score / solved), 2) if solved > 0 else 0.0
            rows.append({
                'rank': offset + idx + 1,
                'user_id': str(user.pk),
                'username': user.username,
                'display_name': user.display_name or user.username,
                'avatar_url': user.avatar_url,
                'score': int(score),
                'problems_solved': solved,
                'avg_score': avg_score,
                'weekly_delta': (
                    previous_rank_map[str(user.pk)] - (offset + idx + 1)
                    if str(user.pk) in previous_rank_map
                    else None
                ),
            })
        return rows

    def get(self, request):
        period = _normalize_period(request.query_params.get('period', 'all_time'))
        page = max(1, int(request.query_params.get('page', 1)))
        limit = max(1, min(100, int(request.query_params.get('limit', 25))))
        offset = (page - 1) * limit
        previous_rank_map = _latest_snapshot_rank_map(period)

        cache_key = leaderboard_top_cache_key(period, count=limit, offset=offset)
        cached = cache_get(cache_key)
        if cached is not None:
            public_payload = dict(cached)
        else:
            redis_rows = get_top(period, count=limit, offset=offset)

            if redis_rows:
                results = self._hydrate_rows(redis_rows, offset, previous_rank_map)
            else:
                # Fallback to DB ordering if Redis is cold.
                ordering = {
                    'alltime': '-total_score',
                    'weekly': '-weekly_score',
                    'monthly': '-monthly_score',
                }[period]
                queryset = User.objects.order_by(ordering, 'id').only(
                    'id', 'username', 'display_name', 'avatar_url',
                    'total_score', 'weekly_score', 'monthly_score', 'problems_solved'
                )
                users = list(queryset[offset: offset + limit])
                results = []
                for idx, user in enumerate(users):
                    score = {
                        'alltime': user.total_score,
                        'weekly': user.weekly_score,
                        'monthly': user.monthly_score,
                    }[period]
                    solved = int(user.problems_solved or 0)
                    avg_score = round((score / solved), 2) if solved > 0 else 0.0
                    results.append({
                        'rank': offset + idx + 1,
                        'user_id': str(user.pk),
                        'username': user.username,
                        'display_name': user.display_name or user.username,
                        'avatar_url': user.avatar_url,
                        'score': int(score),
                        'problems_solved': solved,
                        'avg_score': avg_score,
                        'weekly_delta': (
                            previous_rank_map[str(user.pk)] - (offset + idx + 1)
                            if str(user.pk) in previous_rank_map
                            else None
                        ),
                    })

            podium_rows = get_top(period, count=3, offset=0)
            podium = self._hydrate_rows(podium_rows, offset=0, previous_rank_map=previous_rank_map) if podium_rows else []

            public_payload = {
                'period': period,
                'page': page,
                'limit': limit,
                'results': results,
                'podium': podium,
                'has_more': len(results) == limit,
            }
            cache_set(cache_key, public_payload, ttl=CacheTTL.LEADERBOARD_TOP)

        payload = dict(public_payload)
        if request.user.is_authenticated:
            uid = str(request.user.pk)
            rank = get_rank(period, uid)
            if rank is None:
                rank = request.user.global_rank if period == 'alltime' else None

            score = {
                'alltime': request.user.total_score,
                'weekly': request.user.weekly_score,
                'monthly': request.user.monthly_score,
            }[period]
            solved = int(request.user.problems_solved or 0)
            payload['me'] = {
                'user_id': uid,
                'rank': rank,
                'score': int(score),
                'problems_solved': solved,
                'avg_score': round((score / solved), 2) if solved > 0 else 0.0,
                'weekly_delta': (
                    previous_rank_map[uid] - rank
                    if rank is not None and uid in previous_rank_map
                    else None
                ),
            }

        return Response(payload, status=status.HTTP_200_OK)


class GlobalLeaderboardView(generics.ListAPIView):
    """
    Get global leaderboard based on sum of best scores per problem.
    
    GET /api/leaderboard/global/
    
    Ranking logic:
    - For each user, sum their BEST score across all problems
    - Only ACCEPTED submissions count
    - One score per problem (best only)
    
    Response (200 OK):
    [
        {
            "rank": 1,
            "user": "alice",
            "total_score": 2.85,
            "problems_solved": 3
        },
        {
            "rank": 2,
            "user": "bob",
            "total_score": 2.42,
            "problems_solved": 2
        }
    ]
    
    CRITICAL: Computed dynamically from Submission table.
    NO stored leaderboard entries. NO manual updates.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Compute global leaderboard from submissions."""
        try:
            return self._get_leaderboard(request)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("GlobalLeaderboardView failed: %s", e)
            return Response(
                {"error": "Leaderboard unavailable"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_leaderboard(self, request):
        """Compute global leaderboard from submissions."""
        cache_key = leaderboard_top_cache_key('alltime', count=100, offset=0)
        cached = cache_get(cache_key)
        if cached is not None:
            return Response(cached, status=status.HTTP_200_OK)

        # Get all ACCEPTED submissions
        accepted = Submission.objects.filter(
            status='ACCEPTED'
        ).select_related('user', 'problem')
        
        # For each user, track best score per problem
        user_scores = defaultdict(dict)  # {user_id: {problem_id: best_score}}
        user_info = {}  # {user_id: username}
        
        # Get metric direction for each problem (use only/values to avoid loading short_description if missing)
        problem_metrics = {}
        for problem in Problem.objects.only('id', 'metric').all():
            metric = getattr(problem, 'metric', None) or getattr(problem, 'metric_type', 'accuracy')
            metric_name = (metric or 'accuracy').lower()
            problem_metrics[problem.id] = metric_name in LOWER_IS_BETTER_METRICS
        
        # Process all accepted submissions
        for submission in accepted:
            user_id = submission.user_id
            problem_id = submission.problem_id
            score = submission.score
            
            # Store user info
            if user_id not in user_info:
                user_info[user_id] = submission.user.username
            
            # Track best score per problem
            if problem_id not in user_scores[user_id]:
                user_scores[user_id][problem_id] = score
            else:
                # Compare based on metric direction
                is_lower_better = problem_metrics.get(problem_id, False)
                current_best = user_scores[user_id][problem_id]
                
                if is_lower_better:
                    if score < current_best:
                        user_scores[user_id][problem_id] = score
                else:
                    if score > current_best:
                        user_scores[user_id][problem_id] = score
        
        # Calculate total score per user (sum of best scores)
        leaderboard = []
        for user_id, problem_scores in user_scores.items():
            total_score = sum(problem_scores.values())
            leaderboard.append({
                'name': user_info[user_id],
                'user': user_info[user_id],  # Keep both for compatibility
                'score': total_score,
                'total_score': total_score,  # Keep both for compatibility
                'problems_solved': len(problem_scores)
            })
        
        # Sort by score DESC
        leaderboard.sort(key=lambda x: -x['score'])
        
        # Assign ranks
        for idx, entry in enumerate(leaderboard, start=1):
            entry['rank'] = idx
            entry['score'] = round(entry['score'], 4)
            entry['total_score'] = entry['score']  # Keep in sync

        top_100 = leaderboard[:100]
        cache_set(cache_key, top_100, ttl=CacheTTL.LEADERBOARD_TOP)
        return Response(top_100, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_leaderboard_position(request):
    """
    Get current user's leaderboard position and nearby rankings
    """
    entry, created = LeaderboardEntry.objects.get_or_create(user=request.user)
    
    if created or entry.rank == 0:
        # First time or needs recalculation
        entry.update_stats()
        from .signals import recalculate_ranks
        recalculate_ranks()
        entry.refresh_from_db()
    
    # Get user's position
    serializer = LeaderboardEntrySerializer(entry)
    
    # Get nearby entries (5 above, 5 below)
    rank = entry.rank
    nearby = LeaderboardEntry.objects.filter(
        rank__gte=max(1, rank - 5),
        rank__lte=rank + 5
    ).select_related('user').order_by('rank')
    
    nearby_serializer = LeaderboardEntrySerializer(nearby, many=True)
    
    # Get recent events
    recent_events = LeaderboardEvent.objects.filter(
        user=request.user
    )[:10]
    events_serializer = LeaderboardEventSerializer(recent_events, many=True)
    
    return Response({
        'my_position': serializer.data,
        'nearby_rankings': nearby_serializer.data,
        'recent_events': events_serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_leaderboard(request):
    """
    Manually trigger leaderboard recalculation for current user
    """
    entry, _ = LeaderboardEntry.objects.get_or_create(user=request.user)
    entry.update_stats()
    
    from .signals import recalculate_ranks
    recalculate_ranks()
    
    entry.refresh_from_db()
    serializer = LeaderboardEntrySerializer(entry)
    
    return Response({
        'message': 'Leaderboard refreshed',
        'entry': serializer.data
    })