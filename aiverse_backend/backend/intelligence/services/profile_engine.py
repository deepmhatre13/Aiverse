from __future__ import annotations

from django.db.models import Avg, Count
from django.utils import timezone

from intelligence.models import ExperimentRun, UserProfile
from utils.cache import cache_bust, cache_get, cache_set


DEFAULT_LOW_ACCURACY_THRESHOLD = 0.70
DEFAULT_HIGH_ACCURACY_THRESHOLD = 0.85
PROFILE_UPDATE_COOLDOWN_SECONDS = 300


def _profile_cache_key(user_id) -> str:
    return f"intelligence:profile:{user_id}"


def _profile_update_cooldown_key(user_id) -> str:
    return f"intelligence:profile_update:cooldown:{user_id}"


def _skill_level_from_avg(avg_score: float) -> str:
    if avg_score >= 0.80:
        return UserProfile.SKILL_ADVANCED
    if avg_score >= 0.60:
        return UserProfile.SKILL_INTERMEDIATE
    return UserProfile.SKILL_BEGINNER


def update_user_profile(user) -> UserProfile | None:
    """Recompute and persist a user's intelligence profile from ExperimentRun history."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Lightweight guard to avoid expensive recompute storms under load.
    if cache_get(_profile_update_cooldown_key(user.pk)):
        return profile

    qs = ExperimentRun.objects.filter(user=user).order_by("-created_at")

    total_runs = qs.count()
    avg_score = qs.filter(accuracy__isnull=False).aggregate(v=Avg("accuracy"))["v"] or 0.0

    preferred_models = list(
        qs.exclude(model_type="")
        .values("model_type")
        .annotate(run_count=Count("id"))
        .order_by("-run_count", "model_type")
        .values_list("model_type", flat=True)[:5]
    )

    task_stats = list(
        qs.exclude(task_type="")
        .filter(accuracy__isnull=False)
        .values("task_type")
        .annotate(avg_accuracy=Avg("accuracy"), run_count=Count("id"))
    )
    model_stats = list(
        qs.exclude(model_type="")
        .filter(accuracy__isnull=False)
        .values("model_type")
        .annotate(avg_accuracy=Avg("accuracy"), run_count=Count("id"))
    )

    weaknesses = []
    for row in task_stats:
        if (row.get("avg_accuracy") or 0.0) < DEFAULT_LOW_ACCURACY_THRESHOLD:
            weaknesses.append(row["task_type"])
    for row in model_stats:
        if (row.get("avg_accuracy") or 0.0) < DEFAULT_LOW_ACCURACY_THRESHOLD:
            weaknesses.append(f"model:{row['model_type']}")

    strengths = [
        row["task_type"]
        for row in task_stats
        if (row.get("avg_accuracy") or 0.0) > DEFAULT_HIGH_ACCURACY_THRESHOLD and (row.get("run_count") or 0) >= 3
    ]

    profile.avg_score = float(avg_score)
    profile.total_runs = int(total_runs)
    profile.preferred_models = preferred_models
    profile.weaknesses = sorted(set(weaknesses))[:50]
    profile.strengths = sorted(set(strengths))[:50]
    profile.last_active = profile.last_active or timezone.now()
    profile.skill_level = _skill_level_from_avg(profile.avg_score)

    profile.save(
        update_fields=[
            "avg_score",
            "total_runs",
            "preferred_models",
            "weaknesses",
            "strengths",
            "skill_level",
            "last_active",
        ]
    )

    cache_set(_profile_update_cooldown_key(user.pk), True, ttl=PROFILE_UPDATE_COOLDOWN_SECONDS)
    cache_bust(_profile_cache_key(user.pk))
    return profile

