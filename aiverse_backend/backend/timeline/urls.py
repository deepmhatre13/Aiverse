from django.urls import path
from . import views

app_name = 'timeline'

urlpatterns = [
    path('activity/', views.ActivityEventListView.as_view(), name='activity-list'),
    path('performance/', views.PerformanceSnapshotListView.as_view(), name='performance-list'),
    path('summary/', views.timeline_summary, name='summary'),
    path('snapshot/generate/', views.generate_snapshot, name='generate-snapshot'),
]