"""
Notifications & Achievements Views

Django REST Framework views for notifications and achievements.
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import logging

from .models import Notification, Achievement, UserAchievement, Milestone, UserMilestone
from .serializers import (
    NotificationSerializer, 
    AchievementSerializer, 
    UserAchievementSerializer,
    MilestoneSerializer
)
from .services import NotificationService, AchievementService, MilestoneService

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Get notifications for current user."""
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(generics.UpdateAPIView):
    """Mark a notification as read."""
    permission_classes = [IsAuthenticated]
    
    def update(self, request, notification_id=None):
        """Mark notification as read."""
        try:
            notification_service = NotificationService()
            success = notification_service.mark_as_read(
                user_id=request.user.id,
                notification_id=notification_id
            )
            
            if success:
                return Response({'status': 'success', 'message': 'Notification marked as read'})
            else:
                return Response(
                    {'error': 'Notification not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return Response(
                {'error': 'Failed to mark notification as read'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckNotificationsView(generics.GenericAPIView):
    """Check and create notifications for the current user."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Trigger notification check."""
        try:
            from .tasks import check_user_notifications_task
            
            # Trigger async task
            check_user_notifications_task.delay(request.user.id)
            
            return Response({
                'status': 'success',
                'message': 'Notification check triggered'
            })
        except Exception as e:
            logger.error(f"Error triggering notification check: {e}")
            return Response(
                {'error': 'Failed to trigger notification check'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AchievementListView(generics.ListAPIView):
    """List achievements for the current user."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAchievementSerializer
    
    def get_queryset(self):
        """Get achievements for current user."""
        return UserAchievement.objects.filter(user=self.request.user)


class AvailableAchievementsView(generics.ListAPIView):
    """List all available achievements with earned status."""
    permission_classes = [IsAuthenticated]
    serializer_class = AchievementSerializer
    
    def get_queryset(self):
        """Get all active achievements."""
        return Achievement.objects.filter(is_active=True)
    
    def list(self, request):
        """List achievements with earned status."""
        try:
            achievement_service = AchievementService()
            achievements = achievement_service.get_available_achievements(request.user.id)
            
            return Response({
                'achievements': achievements,
                'total': len(achievements)
            })
        except Exception as e:
            logger.error(f"Error getting available achievements: {e}")
            return Response(
                {'error': 'Failed to get achievements'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckAchievementsView(generics.GenericAPIView):
    """Check and award achievements for the current user."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Trigger achievement check."""
        try:
            achievement_service = AchievementService()
            new_achievements = achievement_service.check_achievements(request.user.id)
            
            return Response({
                'status': 'success',
                'new_achievements': len(new_achievements),
                'achievements': [
                    {
                        'name': a.name,
                        'icon': a.icon,
                        'points': a.points
                    }
                    for a in new_achievements
                ]
            })
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
            return Response(
                {'error': 'Failed to check achievements'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MilestoneListView(generics.ListAPIView):
    """List milestones for the current user."""
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer
    
    def get_queryset(self):
        """Get milestones for current user."""
        return Milestone.objects.all()


class UpdateMilestonesView(generics.GenericAPIView):
    """Update milestones for the current user."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Trigger milestone update."""
        try:
            milestone_service = MilestoneService()
            newly_completed = milestone_service.update_user_milestones(request.user.id)
            
            return Response({
                'status': 'success',
                'newly_completed': len(newly_completed),
                'milestones': [
                    {
                        'name': m.name,
                        'description': m.description
                    }
                    for m in newly_completed
                ]
            })
        except Exception as e:
            logger.error(f"Error updating milestones: {e}")
            return Response(
                {'error': 'Failed to update milestones'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )