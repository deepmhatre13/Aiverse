from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('overview/', views.dashboard_overview, name='overview'),
    path('timeline/', views.TimelineView.as_view(), name='timeline'),
    path('submissions/', views.SubmissionHistoryView.as_view(), name='submissions'),
    path('performance/', views.PerformanceView.as_view(), name='performance'),

    # Live Performance Center API
    path('live-metrics/', views.LiveMetricsView.as_view(), name='live-metrics'),
]