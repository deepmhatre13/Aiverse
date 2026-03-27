"""3-layer cache helpers (L1 memory + L2 Redis/Django cache + DB fallback).

L1: process-local in-memory LRU-ish cache
L2: Django cache backend (configured to Redis in settings)
L3: caller-provided source of truth (usually database query)
"""
from collections import OrderedDict
from threading import Lock
from time import time

from django.core.cache import cache


L1_MAX_ITEMS = 1024
_l1_store = OrderedDict()
_l1_lock = Lock()


class CacheTTL:
    PROFILE = 30
    CATEGORIES = 3600
    PROBLEMS_LIST = 300
    LEADERBOARD_TOP = 30
    SUBMISSION = 300


def _l1_get(key: str):
    now = time()
    with _l1_lock:
        item = _l1_store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at <= now:
            _l1_store.pop(key, None)
            return None
        _l1_store.move_to_end(key)
        return value


def _l1_set(key: str, value, ttl: int):
    expires_at = time() + max(ttl, 1)
    with _l1_lock:
        _l1_store[key] = (expires_at, value)
        _l1_store.move_to_end(key)
        while len(_l1_store) > L1_MAX_ITEMS:
            _l1_store.popitem(last=False)


def _l1_delete(key: str):
    with _l1_lock:
        _l1_store.pop(key, None)


def cache_get(key: str):
    value = _l1_get(key)
    if value is not None:
        return value

    value = cache.get(key)
    if value is not None:
        _l1_set(key, value, 30)
    return value


def cache_set(key: str, value, ttl: int = 30):
    """Set cache value with TTL in seconds across L1 and L2."""
    _l1_set(key, value, ttl)
    cache.set(key, value, timeout=ttl)


def cache_bust(*keys: str):
    """Delete one or more cache keys from L1 and L2."""
    for key in keys:
        _l1_delete(key)
        cache.delete(key)


def cache_get_or_set(key: str, callable_fn, ttl: int = 30):
    """Get from cache or compute via callable and store in L1/L2."""
    val = cache_get(key)
    if val is None:
        val = callable_fn()
        cache_set(key, val, ttl=ttl)
    return val


def profile_cache_key(user_id) -> str:
    return f'profile:{user_id}'


def categories_cache_key() -> str:
    return 'categories:all'


def problems_list_cache_key() -> str:
    return 'problems:list'


def submission_cache_key(submission_id) -> str:
    return f'submission:{submission_id}'


def leaderboard_top_cache_key(period: str = 'alltime', count: int = 100, offset: int = 0) -> str:
    return f'leaderboard:{period}:top:{offset}:{count}'


def leaderboard_hot_cache_keys() -> list:
    """Common leaderboard cache keys likely to be requested by UI.

    We proactively invalidate these after rank/score mutations.
    """
    keys = []
    for period in ('alltime', 'weekly', 'monthly'):
        keys.append(leaderboard_top_cache_key(period, count=100, offset=0))
        keys.append(leaderboard_top_cache_key(period, count=25, offset=0))
    return keys
