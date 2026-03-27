from django.urls import path
from .views import (
    ProblemListView,
    ProblemDetailView,
    ProblemEvaluateView,
    ProblemSubmitView,
    ProblemSubmissionsView,
    SubmissionListView,
    SubmissionDetailView,
    ProblemRunView,
    ProblemLeaderboardView,
)

app_name = 'ml'

urlpatterns = [
    path('problems/', ProblemListView.as_view(), name='problem-list'),
    path('problems/<slug:slug>/', ProblemDetailView.as_view(), name='problem-detail'),
    path('problems/<slug:slug>/evaluate/', ProblemEvaluateView.as_view(), name='problem-evaluate'),
    path('problems/<slug:slug>/submit/', ProblemSubmitView.as_view(), name='problem-submit'),
    path('problems/<slug:slug>/submissions/', ProblemSubmissionsView.as_view(), name='problem-submissions'),
    path('problems/<slug:slug>/leaderboard/', ProblemLeaderboardView.as_view(), name='problem-leaderboard'),
    path('submissions/', SubmissionListView.as_view(), name='submission-list'),
    path('submissions/<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
    path('problems/<slug:slug>/run/',ProblemRunView.as_view(),name='problem-run'),
]