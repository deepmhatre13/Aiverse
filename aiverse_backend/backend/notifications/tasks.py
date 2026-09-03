"""
Notifications & Achievements Celery Tasks

Asynchronous tasks for notifications and achievements.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .services import NotificationService, AchievementService, MilestoneService, check_and_send_notifications

logger = logging.getLogger(__name__)


@shared_task
def check_user_notifications_task(user_id: int):
    """
    Check and send notifications for a user.
    
    Args:
        user_id: User ID
    """
    try:
        check_and_send_notifications(user_id)
        logger.info(f"Notification check completed for user {user_id}")
    except Exception as e:
        logger.error(f"Error in notification check task for user {user_id}: {e}")


@shared_task
def batch_check_notifications_task():
    """
    Check notifications for all active users.
    Runs periodically (e.g., every hour).
    """
    try:
        from django.contrib.auth import get_user_model
        from datetime import datetime, timedelta
        
        User = get_user_model()
        
        # Get users active in last 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(last_login__gte=cutoff_date)
        
        user_ids = list(active_users.values_list('id', flat=True))
        
        # Trigger async checks
        for user_id in user_ids:
            check_user_notifications_task.delay(user_id)
        
        logger.info(f"Triggered notification checks for {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Error in batch notification check: {e}")


@shared_task
def send_pending_notifications_task():
    """
    Send all pending notifications.
    Runs periodically (e.g., every 5 minutes).
    """
    try:
        notification_service = NotificationService()
        sent_count = notification_service.send_pending_notifications()
        logger.info(f"Sent {sent_count} pending notifications")
    except Exception as e:
        logger.error(f"Error sending pending notifications: {e}")


@shared_task
def check_user_achievements_task(user_id: int):
    """
    Check and award achievements for a user.
    
    Args:
        user_id: User ID
    """
    try:
        achievement_service = AchievementService()
        new_achievements = achievement_service.check_achievements(user_id)
        
        if new_achievements:
            logger.info(f"Awarded {len(new_achievements)} achievements to user {user_id}")
        else:
            logger.info(f"No new achievements for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error checking achievements for user {user_id}: {e}")


@shared_task
def batch_check_achievements_task():
    """
    Check achievements for all users.
    Runs daily.
    """
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user_ids = list(User.objects.values_list('id', flat=True))
        
        # Trigger async checks
        for user_id in user_ids:
            check_user_achievements_task.delay(user_id)
        
        logger.info(f"Triggered achievement checks for {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Error in batch achievement check: {e}")


@shared_task
def update_user_milestones_task(user_id: int):
    """
    Update milestones for a user.
    
    Args:
        user_id: User ID
    """
    try:
        milestone_service = MilestoneService()
        newly_completed = milestone_service.update_user_milestones(user_id)
        
        if newly_completed:
            logger.info(f"Completed {len(newly_completed)} milestones for user {user_id}")
        else:
            logger.info(f"No new milestones for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error updating milestones for user {user_id}: {e}")


@shared_task
def batch_update_milestones_task():
    """
    Update milestones for all users.
    Runs daily.
    """
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user_ids = list(User.objects.values_list('id', flat=True))
        
        # Trigger async updates
        for user_id in user_ids:
            update_user_milestones_task.delay(user_id)
        
        logger.info(f"Triggered milestone updates for {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Error in batch milestone update: {e}")


@shared_task
def cleanup_old_notifications_task():
    """
    Delete old read notifications (older than 30 days).
    Runs daily.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_count, _ = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Deleted {deleted_count} old notifications")
    except Exception as e:
        logger.error(f"Error cleaning up old notifications: {e}")


@shared_task
def generate_daily_recommendations_task(user_id: int):
    """
    Generate daily recommendations for a user.

    Delegates to the existing in-process RuleBasedRecommender (deterministic,
    explainable). This replaces a previously-broken implementation that
    imported the external `aiverse_ml_service` package (not importable from
    the Django process) and called an undefined `store_recommendations`.

    Args:
        user_id: User ID
    """
    try:
        from recommendations.services import RuleBasedRecommender

        recommender = RuleBasedRecommender(user_id)
        recommender.generate_and_cache()

        logger.info(f"Generated daily recommendations for user {user_id}")
    except Exception as e:
        logger.error(f"Error generating daily recommendations for user {user_id}: {e}")


@shared_task
def batch_generate_daily_recommendations_task():
    """
    Generate daily recommendations for all active users.
    Runs daily.
    """
    try:
        from django.contrib.auth import get_user_model
        from datetime import datetime, timedelta
        
        User = get_user_model()
        
        # Get users active in last 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        active_users = User.objects.filter(last_login__gte=cutoff_date)
        
        user_ids = list(active_users.values_list('id', flat=True))
        
        # Trigger async generation
        for user_id in user_ids:
            generate_daily_recommendations_task.delay(user_id)
        
        logger.info(f"Triggered daily recommendation generation for {len(user_ids)} users")
    except Exception as e:
        logger.error(f"Error in batch daily recommendations: {e}")


@shared_task
def trigger_notification_on_event(user_id: int, event_type: str, event_data: Dict[str, Any]):
    """
    Trigger notifications based on learner events.
    
    Args:
        user_id: User ID
        event_type: Type of event
        event_data: Event data
    """
    try:
        notification_service = NotificationService()
        
        # Check for achievement-worthy events
        if event_type in ['QUIZ_PASSED', 'CODE_PASSED', 'CONCEPT_MASTERED']:
            # Check achievements
            achievement_service = AchievementService()
            new_achievements = achievement_service.check_achievements(user_id)
            
            if new_achievements:
                logger.info(f"Event triggered {len(new_achievements)} achievements for user {user_id}")
        
        # Check for weak topic state changes
        if event_type in ['QUIZ_FAILED', 'CODE_FAILED']:
            from learner.services.weak_topic_analyzer import WeakTopicAnalyzer
            
            analyzer = WeakTopicAnalyzer(user_id)
            weak_topics = analyzer.analyze_user_weak_topics()
            
            for topic in weak_topics:
                if topic.get('is_struggling') and topic.get('quiz_attempts', 0) >= 3:
                    notification_service.create_notification(
                        user_id=user_id,
                        notification_type='struggling_state_change',
                        title=f"Struggling with {topic['concept_tag']}",
                        message=f"You're struggling with {topic['concept_tag']}. Here's a review lesson to help.",
                        channel='in_app',
                        data={'concept_tag': topic['concept_tag']}
                    )
                    break  # Only notify for one topic at a time
        
        logger.info(f"Processed notification triggers for user {user_id}, event {event_type}")
    
    except Exception as e:
        logger.error(f"Error triggering notification on event: {e}")