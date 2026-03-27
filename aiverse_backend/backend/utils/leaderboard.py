"""Redis utilities for leaderboard sorted sets."""
import os

from redis import Redis


def _redis_url() -> str:
    host = os.environ.get('REDIS_HOST', '127.0.0.1')
    port = os.environ.get('REDIS_PORT', '6379')
    return os.environ.get('REDIS_URL', f'redis://{host}:{port}/0')


def get_redis():
    """Get a Redis connection for sorted set operations."""
    return Redis.from_url(_redis_url(), decode_responses=True)


def zadd_score(period: str, user_id: str, score: int):
    """ZADD leaderboard:{period} user_id score."""
    try:
        r = get_redis()
        key = f'leaderboard:{period}'
        r.zadd(key, {user_id: int(score)})
    except Exception:
        pass


def get_rank(period: str, user_id: str):
    """ZREVRANK leaderboard:{period} user_id — returns 1-based rank or None."""
    try:
        r = get_redis()
        key = f'leaderboard:{period}'
        rank = r.zrevrank(key, user_id)
        return (rank + 1) if rank is not None else None
    except Exception:
        return None


def get_top(period: str, count: int = 100, offset: int = 0):
    """ZREVRANGE with scores — returns list of (user_id, score)."""
    try:
        r = get_redis()
        key = f'leaderboard:{period}'
        entries = r.zrevrange(key, offset, offset + count - 1, withscores=True)
        return [(uid, int(score)) for uid, score in entries]
    except Exception:
        return []


def delete_leaderboard(period: str):
    """DEL leaderboard:{period}."""
    try:
        r = get_redis()
        r.delete(f'leaderboard:{period}')
    except Exception:
        pass


def zadd_scores_atomic(user_id: str, total_score: int, weekly_score: int, monthly_score: int):
    """Atomically update all leaderboard sorted sets for a user."""
    try:
        r = get_redis()
        with r.pipeline(transaction=True) as pipe:
            pipe.zadd('leaderboard:alltime', {user_id: int(total_score)})
            pipe.zadd('leaderboard:weekly', {user_id: int(weekly_score)})
            pipe.zadd('leaderboard:monthly', {user_id: int(monthly_score)})
            pipe.execute()
    except Exception:
        pass
