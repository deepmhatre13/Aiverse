from django.urls import path
from . import views

app_name = 'leaderboard'

urlpatterns = [
    path('', views.LeaderboardListView.as_view(), name='list'),
    path('global/', views.GlobalLeaderboardView.as_view(), name='global'),
    path('me/', views.my_leaderboard_position, name='my-position'),
    path('refresh/', views.refresh_leaderboard, name='refresh'),
]