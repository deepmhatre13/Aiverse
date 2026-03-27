"""
ML API URL routing.
"""

from django.urls import path
from .views_ml import (
    ProblemDetailView,
    EvaluateView,
    SubmitView,
    LeaderboardView,
    UserRankView,
    SubmissionHistoryView,
)

urlpatterns = [
    # Problem details
    path('problems/<slug:slug>/', ProblemDetailView.as_view(), name='problem-detail'),
    
    # Evaluation (stateless)
    path('problems/<slug:slug>/evaluate/', EvaluateView.as_view(), name='evaluate'),
    
    # Submission (stateful)
    path('problems/<slug:slug>/submit/', SubmitView.as_view(), name='submit'),
    
    # Leaderboard
    path('problems/<slug:slug>/leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    
    # User rank
    path('problems/<slug:slug>/my-rank/', UserRankView.as_view(), name='user-rank'),
    
    # Submission history
    path('problems/<slug:slug>/submissions/', SubmissionHistoryView.as_view(), name='submission-history'),
]
