from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.SubmitView.as_view(), name='submit'),
    path('run/', views.RunView.as_view(), name='run'),
    path('recent/', views.RecentSubmissionsView.as_view(), name='recent-submissions'),
    path('heatmap/', views.HeatmapView.as_view(), name='heatmap'),
]
