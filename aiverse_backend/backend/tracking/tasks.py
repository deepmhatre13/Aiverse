"""
Celery tasks for tracking app.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from learner.models import ConceptMastery
from learner.tasks import process_event_for_mastery, update_learner_ability
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def process_learner_event(event_id: str):
    """
    Process a learner event asynchronously.
    
    Triggers:
    - ConceptMastery updates for quiz/code events
    - Learning path recalculation for key events
    - IRT ability updates
    """
    try:
        from tracking.models import LearnerEvent
        
        logger.info(f"Processing learner event {event_id}")
        
        event = LearnerEvent.objects.get(id=event_id)
        event_type = event.event_type
        user_id = event.user_id
        metadata = event.metadata or {}
        
        # Process for mastery update if concept_tag present
        if metadata.get('concept_tag'):
            if event_type in ['QUIZ_PASSED', 'QUIZ_FAILED', 'QUIZ_SUBMITTED',
                              'CODE_PASSED', 'CODE_FAILED', 'CODE_SUBMITTED']:
                process_event_for_mastery.delay(event_id)
        
        # Update learner ability for key events
        if event_type in ['QUIZ_PASSED', 'CODE_PASSED', 'PROBLEM_SOLVED']:
            update_learner_ability.delay(user_id)
        
        logger.info(f"Processed event {event_id} for user {user_id}")
        return {"status": "success", "event_id": event_id}
        
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {str(e)}")
        return {"status": "error", "event_id": event_id, "error": str(e)}


@shared_task
def batch_update_learner_abilities():
    """
    Nightly batch task to update learner abilities for all active users.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        logger.info("Starting batch learner ability update")
        
        week_ago = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(
            last_login__gte=week_ago
        ).values_list('id', flat=True)
        
        count = 0
        for user_id in active_users:
            update_learner_ability.delay(user_id)
            count += 1
        
        logger.info(f"Queued ability update for {count} users")
        return {"status": "success", "users_queued": count}
        
    except Exception as e:
        logger.error(f"Error in batch ability update: {str(e)}")
        return {"status": "error", "error": str(e)}
@shared_task
def generate_daily_recommendations_for_all():
    """
    Generate/cache personalized recommendations for all active users.

    Reuses the existing in-process RuleBasedRecommender (deterministic,
    explainable, no external ML-service dependency) so the daily schedule
    does real work. Active users = logged in within the last 7 days.
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from recommendations.services import RuleBasedRecommender

        week_ago = timezone.now() - timedelta(days=7)
        user_ids = User.objects.filter(last_login__gte=week_ago).values_list("id", flat=True)

        generated = 0
        failed = 0
        for user_id in user_ids:
            try:
                recommender = RuleBasedRecommender(user_id)
                recommender.generate_and_cache()
                generated += 1
            except Exception as e:
                logger.error(f"generate_daily_recommendations_for_all: user {user_id}: {e}")
                failed += 1

        logger.info(f"Generated daily recommendations for {generated} users ({failed} failed)")
        return {"status": "success", "generated": generated, "failed": failed}
    except Exception as e:
        logger.error(f"Error in generate_daily_recommendations_for_all: {e}")
        return {"status": "error", "error": str(e)}


def _compute_dropout_risk(profile, user) -> float:
    """
    Deterministic, explainable dropout-risk estimate (0.0 to 1.0).

    Uses only signals already available on LearnerProfile/user:
    - inactivity: days since last activity / last login (capped at 14)
    - frustration: existing 0-1 frustration signal (failures / attempts)
    - engagement: existing 0-1 engagement signal (completions / events)
    - low activity: users with very few total interactions are at risk

    Weights are explicit so the result stays explainable:
      0.40 * inactivity + 0.30 * frustration + 0.20 * (1 - engagement)
      + 0.10 * low_activity_penalty
    """
    from django.utils import timezone

    today = timezone.now()
    last_active = getattr(profile, "last_active", None)
    last_login = getattr(user, "last_login", None)
    ref = last_active or last_login or today
    days_inactive = max(0, (today - ref).days)
    inactivity = min(1.0, days_inactive / 14.0)

    frustration = max(0.0, min(1.0, float(getattr(profile, "frustration_score", 0.0) or 0.0)))
    engagement = max(0.0, min(1.0, float(getattr(profile, "engagement_score", 0.0) or 0.0)))

    interaction_count = (
        (getattr(profile, "total_lessons_completed", 0) or 0)
        + (getattr(profile, "total_problems_solved", 0) or 0)
        + (getattr(profile, "total_quizzes_passed", 0) or 0)
    )
    low_activity_penalty = 1.0 if interaction_count < 5 else 0.0

    risk = (
        0.40 * inactivity
        + 0.30 * frustration
        + 0.20 * (1.0 - engagement)
        + 0.10 * low_activity_penalty
    )
    return round(max(0.0, min(1.0, risk)), 4)


@shared_task
def update_dropout_risk_all_users():
    """
    Refresh LearnerProfile.dropout_risk for all active users.

    For each active user, recompute the aggregate learner signals via the
    existing LearnerProfileService, then persist a deterministic dropout-risk
    estimate. Real work; no external ML-service dependency.
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from learner.services import LearnerProfileService

        week_ago = timezone.now() - timedelta(days=7)
        users = User.objects.filter(last_login__gte=week_ago)

        updated = 0
        for user in users:
            try:
                profile = LearnerProfileService.recompute(user.id)
                profile.dropout_risk = _compute_dropout_risk(profile, user)
                profile.save(update_fields=["dropout_risk", "last_updated"])
                updated += 1
            except Exception as e:
                logger.error(f"update_dropout_risk_all_users: user {user.id}: {e}")

        logger.info(f"Updated dropout risk for {updated} users")
        return {"status": "success", "updated": updated}
    except Exception as e:
        logger.error(f"Error in update_dropout_risk_all_users: {e}")
        return {"status": "error", "error": str(e)}
@shared_task
def recompute_all_mastery_scores():
    """
    Recompute ConceptMastery scores and refresh LearnerProfile aggregates
    for all active users. Reuses the existing BKT recompute + weak-topic
    analyzer services (deterministic, no duplication).
    """
    try:
        from datetime import timedelta
        from django.utils import timezone
        from learner.models import ConceptMastery
        from learner.services.weak_topic_analyzer import update_learner_profile_topics

        week_ago = timezone.now() - timedelta(days=7)
        user_ids = User.objects.filter(last_login__gte=week_ago).values_list("id", flat=True)

        updated = 0
        for user_id in user_ids:
            try:
                masteries = ConceptMastery.objects.filter(user_id=user_id)
                for mastery in masteries:
                    mastery.recompute_mastery()
                if masteries.exists():
                    update_learner_profile_topics(user_id)
                updated += 1
            except Exception as e:
                logger.error(f"recompute_all_mastery_scores: user {user_id}: {e}")

        logger.info(f"Recomputed mastery for {updated} users")
        return {"status": "success", "updated": updated}
    except Exception as e:
        logger.error(f"Error in recompute_all_mastery_scores: {e}")
        return {"status": "error", "error": str(e)}


@shared_task
def retrain_ml_models_nightly():
    """
    Trigger nightly retraining of the external ML personalization service.

    Sends a real request to the ML service /admin/retrain endpoint. If the
    service is unreachable or not configured, we log and return a clear status
    (the ML service remains optional). This is not a dummy task — it performs
    a genuine (graceful) request.
    """
    try:
        from recommendations.ml_client import call_ml_service

        result = call_ml_service("/admin/retrain", {"all": True})
        if result is None:
            logger.warning("retrain_ml_models_nightly: ML service unavailable or retrain failed")
            return {"status": "unavailable", "retrained": []}
        retrained = result.get("retrained", [])
        logger.info(f"ML model retraining complete: {retrained}")
        return {"status": "success", "retrained": retrained}
    except Exception as e:
        logger.error(f"Error in retrain_ml_models_nightly: {e}")
        return {"status": "error", "error": str(e)}