"""
Notifications & Achievements URLs

URL routing for notifications and achievements endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
    path('notifications/check/', views.CheckNotificationsView.as_view(), name='notification-check'),
    
    # Achievements
    path('achievements/', views.AchievementListView.as_view(), name='achievement-list'),
    path('achievements/available/', views.AvailableAchievementsView.as_view(), name='available-achievements'),
    path('achievements/check/', views.CheckAchievementsView.as_view(), name='achievement-check'),
    
    # Milestones
    path('milestones/', views.MilestoneListView.as_view(), name='milestone-list'),
    path('milestones/update/', views.UpdateMilestonesView.as_view(), name='milestone-update'),
]