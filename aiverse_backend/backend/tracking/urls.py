from django.urls import path
from . import views

urlpatterns = [
    path('track/', views.TrackEventView.as_view(), name='track-event'),
    path('track/batch/', views.BatchTrackEventView.as_view(), name='batch-track'),
    path('history/', views.UserEventHistoryView.as_view(), name='event-history'),
]
