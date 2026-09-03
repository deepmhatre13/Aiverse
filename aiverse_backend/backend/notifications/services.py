"""
Notifications & Achievements Service

Service for managing notifications and achievements.
"""

from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db.models import Count, Max
from datetime import timedelta
import logging

from .models import Notification, Achievement, UserAchievement, Milestone, UserMilestone, NotificationTemplate

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing user notifications."""
    
    def create_notification(self, user_id: int, notification_type: str, 
                          title: str, message: str, channel: str = 'in_app',
                          data: Dict[str, Any] = None, scheduled_for: Optional[timezone.datetime] = None) -> Notification:
        """
        Create a notification for a user.
        
        Args:
            user_id: User ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            channel: Notification channel (push, email, in_app, sms)
            data: Additional metadata
            scheduled_for: When to send the notification
            
        Returns:
            Notification object
        """
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                channel=channel,
                title=title,
                message=message,
                data=data or {},
                scheduled_for=scheduled_for
            )
            
            logger.info(f"Created notification for user {user_id}: {notification_type}")
            return notification
        
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")
            raise
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, 
                              limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification dicts
        """
        try:
            queryset = Notification.objects.filter(user_id=user_id)
            
            if unread_only:
                queryset = queryset.filter(is_read=False)
            
            notifications = queryset[:limit]
            
            return [
                {
                    'id': n.id,
                    'notification_type': n.notification_type,
                    'channel': n.channel,
                    'title': n.title,
                    'message': n.message,
                    'data': n.data,
                    'is_read': n.is_read,
                    'is_sent': n.is_sent,
                    'created_at': n.created_at.isoformat(),
                    'scheduled_for': n.scheduled_for.isoformat() if n.scheduled_for else None
                }
                for n in notifications
            ]
        
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            return []
    
    def mark_as_read(self, user_id: int, notification_id: int) -> bool:
        """
        Mark a notification as read.
        
        Args:
            user_id: User ID
            notification_id: Notification ID
            
        Returns:
            True if successful
        """
        try:
            notification = Notification.objects.get(id=notification_id, user_id=user_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} not found for user {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def send_pending_notifications(self) -> int:
        """
        Send all pending notifications that are due.
        
        Returns:
            Number of notifications sent
        """
        try:
            now = timezone.now()
            pending = Notification.objects.filter(
                is_sent=False,
                scheduled_for__lte=now
            )
            
            sent_count = 0
            for notification in pending:
                try:
                    self._send_notification(notification)
                    notification.mark_as_sent()
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error sending notification {notification.id}: {e}")
            
            logger.info(f"Sent {sent_count} notifications")
            return sent_count
        
        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")
            return 0
    
    def _send_notification(self, notification: Notification):
        """
        Send a notification via the appropriate channel.
        
        Args:
            notification: Notification object
        """
        # In production, integrate with actual notification services:
        # - Push: Firebase Cloud Messaging / OneSignal
        # - Email: SendGrid / AWS SES
        # - SMS: Twilio
        # - In-app: Store in database (already done)
        
        logger.info(f"Sending {notification.channel} notification to user {notification.user_id}: {notification.title}")
        
        # For now, just log
        if notification.channel == 'push':
            # TODO: Integrate FCM/OneSignal
            pass
        elif notification.channel == 'email':
            # TODO: Integrate SendGrid/SES
            pass
        elif notification.channel == 'sms':
            # TODO: Integrate Twilio
            pass


class AchievementService:
    """Service for managing achievements and milestones."""
    
    def check_achievements(self, user_id: int) -> List[Achievement]:
        """
        Check and award achievements for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of newly earned achievements
        """
        try:
            from learner.models import ConceptMastery, LearnerProfile
            from leaderboard.models import LeaderboardEntry
            from learner.services.weak_topic_analyzer import WeakTopicAnalyzer
            
            # Get user's current achievements
            earned_achievements = set(
                UserAchievement.objects.filter(user_id=user_id).values_list('achievement__slug', flat=True)
            )
            
            # Get all active achievements
            all_achievements = Achievement.objects.filter(is_active=True)
            
            new_achievements = []
            
            for achievement in all_achievements:
                # Skip if already earned
                if achievement.slug in earned_achievements:
                    continue
                
                # Check criteria
                if self._check_achievement_criteria(user_id, achievement):
                    self._award_achievement(user_id, achievement)
                    new_achievements.append(achievement)
            
            return new_achievements
        
        except Exception as e:
            logger.error(f"Error checking achievements for user {user_id}: {e}")
            return []
    
    def _check_achievement_criteria(self, user_id: int, achievement: Achievement) -> bool:
        """
        Check if user meets achievement criteria.
        
        Args:
            user_id: User ID
            achievement: Achievement object
            
        Returns:
            True if criteria met
        """
        try:
            criteria = achievement.criteria
            
            if achievement.achievement_type == 'concept_mastery':
                return self._check_concept_mastery_criteria(user_id, criteria)
            elif achievement.achievement_type == 'streak':
                return self._check_streak_criteria(user_id, criteria)
            elif achievement.achievement_type == 'improvement':
                return self._check_improvement_criteria(user_id, criteria)
            elif achievement.achievement_type == 'experiment':
                return self._check_experiment_criteria(user_id, criteria)
            elif achievement.achievement_type == 'milestone':
                return self._check_milestone_criteria(user_id, criteria)
            
            return False
        
        except Exception as e:
            logger.error(f"Error checking criteria for achievement {achievement.slug}: {e}")
            return False
    
    def _check_concept_mastery_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check concept mastery achievement criteria."""
        from learner.models import ConceptMastery
        
        concept_count = criteria.get('concept_count', 0)
        timeframe_days = criteria.get('timeframe_days', None)
        min_mastery = criteria.get('min_mastery', 0.8)
        
        # Get mastered concepts
        masteries = ConceptMastery.objects.filter(user_id=user_id, mastery_score__gte=min_mastery)
        
        if timeframe_days:
            cutoff_date = timezone.now() - timedelta(days=timeframe_days)
            masteries = masteries.filter(updated_at__gte=cutoff_date)
        
        return masteries.count() >= concept_count
    
    def _check_streak_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check streak achievement criteria."""
        from leaderboard.models import LeaderboardEntry
        
        min_streak = criteria.get('min_streak', 0)
        
        try:
            leaderboard = LeaderboardEntry.objects.get(user_id=user_id)
            return leaderboard.streak_days >= min_streak
        except LeaderboardEntry.DoesNotExist:
            return False
    
    def _check_improvement_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check improvement achievement criteria."""
        from learner.services.weak_topic_analyzer import WeakTopicAnalyzer
        
        min_improvement = criteria.get('min_improvement', 0.2)
        timeframe_days = criteria.get('timeframe_days', 7)
        
        analyzer = WeakTopicAnalyzer(user_id)
        weak_topics = analyzer.analyze_user_weak_topics()
        
        # Check if any weak topic improved significantly
        for topic in weak_topics:
            if topic.get('trend') == 'improving':
                # Check if improvement exceeds threshold
                if topic.get('mastery_change', 0) >= min_improvement:
                    return True
        
        return False
    
    def _check_experiment_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check experiment achievement criteria."""
        from playground.models import ExperimentRun
        
        min_experiments = criteria.get('min_experiments', 0)
        timeframe_days = criteria.get('timeframe_days', None)
        
        experiments = ExperimentRun.objects.filter(user_id=user_id)
        
        if timeframe_days:
            cutoff_date = timezone.now() - timedelta(days=timeframe_days)
            experiments = experiments.filter(created_at__gte=cutoff_date)
        
        return experiments.count() >= min_experiments
    
    def _check_milestone_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check milestone achievement criteria."""
        # Similar to milestone checking
        return False
    
    def _award_achievement(self, user_id: int, achievement: Achievement):
        """
        Award an achievement to a user.
        
        Args:
            user_id: User ID
            achievement: Achievement object
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        UserAchievement.objects.create(
            user=user,
            achievement=achievement,
            metadata={'awarded_at': timezone.now().isoformat()}
        )
        
        # Create notification
        notification_service = NotificationService()
        notification_service.create_notification(
            user_id=user_id,
            notification_type='achievement_unlocked',
            title=f"Achievement Unlocked: {achievement.name}",
            message=f"Congratulations! You've earned the '{achievement.name}' achievement. {achievement.description}",
            channel='in_app',
            data={'achievement_slug': achievement.slug, 'points': achievement.points}
        )
        
        logger.info(f"Awarded achievement '{achievement.name}' to user {user_id}")
    
    def get_user_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all achievements for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of achievement dicts
        """
        try:
            user_achievements = UserAchievement.objects.filter(user_id=user_id).select_related('achievement')
            
            return [
                {
                    'id': ua.id,
                    'name': ua.achievement.name,
                    'slug': ua.achievement.slug,
                    'achievement_type': ua.achievement.achievement_type,
                    'description': ua.achievement.description,
                    'icon': ua.achievement.icon,
                    'points': ua.achievement.points,
                    'earned_at': ua.earned_at.isoformat(),
                    'metadata': ua.metadata
                }
                for ua in user_achievements
            ]
        
        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []
    
    def get_available_achievements(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all available achievements with earned status.
        
        Args:
            user_id: User ID
            
        Returns:
            List of achievement dicts with earned status
        """
        try:
            earned_slugs = set(
                UserAchievement.objects.filter(user_id=user_id).values_list('achievement__slug', flat=True)
            )
            
            all_achievements = Achievement.objects.filter(is_active=True)
            
            return [
                {
                    'id': a.id,
                    'name': a.name,
                    'slug': a.slug,
                    'achievement_type': a.achievement_type,
                    'description': a.description,
                    'icon': a.icon,
                    'points': a.points,
                    'criteria': a.criteria,
                    'earned': a.slug in earned_slugs
                }
                for a in all_achievements
            ]
        
        except Exception as e:
            logger.error(f"Error getting available achievements for user {user_id}: {e}")
            return []


class MilestoneService:
    """Service for managing milestones."""
    
    def update_user_milestones(self, user_id: int) -> List[Milestone]:
        """
        Update all milestones for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of newly completed milestones
        """
        try:
            from learner.models import ConceptMastery
            from leaderboard.models import LeaderboardEntry
            
            # Get all active milestones
            milestones = Milestone.objects.filter(is_completed=False)
            
            newly_completed = []
            
            for milestone in milestones:
                current_value = self._get_milestone_value(user_id, milestone)
                
                if current_value >= milestone.target_value:
                    self._complete_milestone(user_id, milestone)
                    newly_completed.append(milestone)
            
            return newly_completed
        
        except Exception as e:
            logger.error(f"Error updating milestones for user {user_id}: {e}")
            return []
    
    def _get_milestone_value(self, user_id: int, milestone: Milestone) -> int:
        """Get current value for a milestone."""
        try:
            if milestone.milestone_type == 'concept':
                from learner.models import ConceptMastery
                return ConceptMastery.objects.filter(
                    user_id=user_id,
                    mastery_score__gte=0.8
                ).count()
            
            elif milestone.milestone_type == 'platform':
                # Platform-wide milestones are global, not per-user
                return milestone.current_value
            
            elif milestone.milestone_type == 'streak':
                from leaderboard.models import LeaderboardEntry
                try:
                    leaderboard = LeaderboardEntry.objects.get(user_id=user_id)
                    return leaderboard.streak_days
                except LeaderboardEntry.DoesNotExist:
                    return 0
            
            elif milestone.milestone_type == 'improvement':
                # Improvement milestones
                return 0
            
            return 0
        
        except Exception as e:
            logger.error(f"Error getting milestone value: {e}")
            return 0
    
    def _complete_milestone(self, user_id: int, milestone: Milestone):
        """
        Complete a milestone for a user.
        
        Args:
            user_id: User ID
            milestone: Milestone object
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Create user milestone record
        UserMilestone.objects.create(
            user=user,
            milestone=milestone
        )
        
        # Create notification
        notification_service = NotificationService()
        notification_service.create_notification(
            user_id=user_id,
            notification_type='achievement_unlocked',
            title=f"Milestone Reached: {milestone.name}",
            message=f"Congratulations! You've reached the milestone: {milestone.description}",
            channel='in_app',
            data={'milestone_id': milestone.id}
        )
        
        logger.info(f"Completed milestone '{milestone.name}' for user {user_id}")


def check_and_send_notifications(user_id: int):
    """
    Check and send notifications for a user.
    
    Args:
        user_id: User ID
    """
    try:
        from learner.services.weak_topic_analyzer import WeakTopicAnalyzer
        from learner.models import ConceptMastery
        from leaderboard.models import LeaderboardEntry
        from aiverse_ml_service.models.spaced_repetition import HalfLifeRegression
        
        notification_service = NotificationService()
        
        # Check for struggling state changes
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
        
        # Check for revision due
        spaced_repetition = HalfLifeRegression()
        reviews = spaced_repetition.get_all_reviews(user_id)
        
        for review in reviews[:5]:  # Top 5 reviews
            if review.get('priority') in ['overdue', 'today']:
                notification_service.create_notification(
                    user_id=user_id,
                    notification_type='revision_due',
                    title=f"Time to review {review['concept_tag']}",
                    message=f"Review {review['concept_tag']} to maintain your knowledge.",
                    channel='in_app',
                    data={'concept_tag': review['concept_tag']}
                )
        
        # Check for streak risk
        try:
            leaderboard = LeaderboardEntry.objects.get(user_id=user_id)
            if leaderboard.streak_days >= 3:
                # Check if user was active yesterday
                yesterday = timezone.now() - timedelta(days=1)
                had_activity = ConceptMastery.objects.filter(
                    user_id=user_id,
                    updated_at__gte=yesterday
                ).exists()
                
                if not had_activity:
                    notification_service.create_notification(
                        user_id=user_id,
                        notification_type='streak_risk',
                        title=f"Your {leaderboard.streak_days}-day streak is at risk!",
                        message=f"Complete a lesson today to keep your {leaderboard.streak_days}-day streak alive!",
                        channel='push',
                        data={'streak_days': leaderboard.streak_days}
                    )
        except LeaderboardEntry.DoesNotExist:
            pass
        
        logger.info(f"Checked notifications for user {user_id}")
    
    except Exception as e:
        logger.error(f"Error checking notifications for user {user_id}: {e}")