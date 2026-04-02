from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from intelligence.models import ExperimentRun, UserActivity, UserProfile


def _get_or_create_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def log_problem_submission(user, problem_id: int, score: float):
    """Log a problem submission attempt and refresh user profile activity timestamp."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    ref_id = _to_int(problem_id)
    safe_score = _to_float(score)

    with transaction.atomic():
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.TYPE_PROBLEM,
            reference_id=ref_id,
            metadata={"score": safe_score},
        )
        profile = _get_or_create_profile(user)
        profile.last_active = timezone.now()
        profile.save(update_fields=["last_active"])
    return True


def log_playground_run(user, dataset: str, model: str, hyperparameters: dict, accuracy: float | None, loss: float | None, task_type: str | None = None, extra_metrics: dict | None = None):
    """Log a completed playground run as both ExperimentRun and UserActivity."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    dataset_name = str(dataset or "")[:255]
    model_type = str(model or "")[:128]
    hyper = hyperparameters if isinstance(hyperparameters, dict) else {}
    safe_extra_metrics = extra_metrics if isinstance(extra_metrics, dict) else {}
    safe_accuracy = _to_float(accuracy)
    safe_loss = _to_float(loss)
    safe_task_type = str(task_type or "")[:64]

    with transaction.atomic():
        run = ExperimentRun.objects.create(
            user=user,
            dataset_name=dataset_name,
            model_type=model_type,
            hyperparameters={**hyper, **safe_extra_metrics},
            accuracy=safe_accuracy,
            loss=safe_loss,
            task_type=safe_task_type,
        )
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.TYPE_PLAYGROUND,
            reference_id=run.id,
            metadata={
                "dataset": dataset_name,
                "model_type": model_type,
                "accuracy": safe_accuracy,
                "loss": safe_loss,
                "task_type": safe_task_type,
            },
        )
        profile = _get_or_create_profile(user)
        profile.last_active = timezone.now()
        profile.save(update_fields=["last_active"])
    return True


def log_mentor_usage(user, query: str):
    """Log a mentor interaction query and refresh user activity timestamp."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    safe_query = str(query or "")[:2000]

    with transaction.atomic():
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.TYPE_MENTOR,
            reference_id=None,
            metadata={"query": safe_query},
        )
        profile = _get_or_create_profile(user)
        profile.last_active = timezone.now()
        profile.save(update_fields=["last_active"])
    return True


def log_learn_access(user, topic: str):
    """Log learn-topic access and refresh user activity timestamp."""
    if not user or not getattr(user, "is_authenticated", False):
        return None

    safe_topic = str(topic or "")[:255]

    with transaction.atomic():
        UserActivity.objects.create(
            user=user,
            activity_type=UserActivity.TYPE_LEARN,
            reference_id=None,
            metadata={"topic": safe_topic},
        )
        profile = _get_or_create_profile(user)
        profile.last_active = timezone.now()
        profile.save(update_fields=["last_active"])
    return True

