from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from intelligence.models import ExperimentRun, SuggestionLog
from utils.cache import cache_get, cache_set


SUGGESTION_COOLDOWN_SECONDS = 300
DEFAULT_LOW_ACCURACY_THRESHOLD = 0.70
SUGGESTION_DEDUPE_WINDOW_SECONDS = 3600


def _cooldown_key(user_id) -> str:
    return f"intelligence:suggestions:cooldown:{user_id}"


def _latest_suggestions(user, limit: int = 5):
    return list(
        SuggestionLog.objects.filter(user=user)
        .order_by("-created_at")
        .values("suggestion_type", "message", "context", "created_at")[:limit]
    )


def _extract_train_test_accuracy(run):
    payload = run.hyperparameters or {}
    train = payload.get("train_accuracy", payload.get("training_accuracy"))
    test = payload.get("test_accuracy", run.accuracy)
    try:
        train = float(train) if train is not None else None
    except (TypeError, ValueError):
        train = None
    try:
        test = float(test) if test is not None else None
    except (TypeError, ValueError):
        test = None
    return train, test


def generate_suggestions(user):
    """Generate user suggestions based on recent runs and return latest 5 suggestion logs."""
    if not user or not getattr(user, "is_authenticated", False):
        return []

    key = _cooldown_key(user.pk)
    if cache_get(key):
        return _latest_suggestions(user=user, limit=5)

    runs = list(ExperimentRun.objects.filter(user=user).order_by("-created_at")[:5])
    if not runs:
        cache_set(key, True, ttl=SUGGESTION_COOLDOWN_SECONDS)
        return []

    latest = runs[0]
    suggestions: list[tuple[str, str, dict]] = []

    # 1) Overfitting detection in any of the last 5 runs.
    for run in runs:
        train_acc, test_acc = _extract_train_test_accuracy(run)
        if train_acc is not None and test_acc is not None and (train_acc - test_acc) > 0.15:
            suggestions.append(
                (
                    "overfitting",
                    "Potential overfitting detected. Try reducing model complexity or adding regularization.",
                    {
                        "run_id": run.id,
                        "model_type": run.model_type,
                        "train_accuracy": train_acc,
                        "test_accuracy": test_acc,
                        "gap": float(train_acc - test_acc),
                    },
                )
            )
            break

    # 2) Low accuracy
    if latest.accuracy is not None and float(latest.accuracy) < DEFAULT_LOW_ACCURACY_THRESHOLD:
        suggestions.append(
            (
                "low_accuracy",
                "Latest run accuracy is low. Try a stronger model or tune hyperparameters.",
                {"accuracy": float(latest.accuracy), "run_id": latest.id, "model_type": latest.model_type},
            )
        )

    # 3) Plateau detection: last 3 runs improvement < 1%
    last3 = [r for r in runs[:3] if r.accuracy is not None]
    if len(last3) == 3:
        a0, a1, a2 = [float(r.accuracy) for r in last3[::-1]]  # oldest -> newest
        improvement = a2 - a0
        if improvement < 0.01:
            suggestions.append(
                (
                    "plateau",
                    "Recent progress has plateaued. Try a different model or feature engineering.",
                    {"oldest": a0, "newest": a2, "improvement": improvement, "run_ids": [r.id for r in last3]},
                )
            )

    # 4) Model bias: last 5 runs all use the same model type.
    last5 = runs[:5]
    if len(last5) == 5:
        model = last5[0].model_type
        if model and all(r.model_type == model for r in last5):
            suggestions.append(
                (
                    "model_bias",
                    "You have used the same model repeatedly. Try a different model for comparison.",
                    {"model_type": model, "run_ids": [r.id for r in last5]},
                )
            )

    # Persist (with per-type one-hour dedupe) and return latest suggestions.
    now = timezone.now()
    dedupe_cutoff = now - timedelta(seconds=SUGGESTION_DEDUPE_WINDOW_SECONDS)
    for suggestion_type, message, context in suggestions:
        duplicate_exists = SuggestionLog.objects.filter(
            user=user,
            suggestion_type=suggestion_type,
            created_at__gte=dedupe_cutoff,
        ).exists()
        if duplicate_exists:
            continue
        SuggestionLog.objects.create(
            user=user,
            suggestion_type=suggestion_type,
            message=message,
            context=context,
        )

    cache_set(key, True, ttl=SUGGESTION_COOLDOWN_SECONDS)
    return _latest_suggestions(user=user, limit=5)

