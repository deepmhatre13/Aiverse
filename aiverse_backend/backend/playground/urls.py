from django.urls import path

from playground.views import (
    DatasetListView,
    ExperimentDetailView,
    ExperimentSelectModelView,
    ExperimentSetHyperparametersView,
    ExperimentStartView,
    ExperimentTrainView,
    PlaygroundCompatJobsView,
    PlaygroundCompatJobDetailView,
    PlaygroundCompatJobMetricsView,
    PlaygroundCompatJobStatusView,
    PlaygroundCompatOptionsView,
)

app_name = 'playground'

urlpatterns = [
    # New real-time training lab API (matches spec)
    path('datasets/', DatasetListView.as_view(), name='datasets'),
    path('experiments/start/', ExperimentStartView.as_view(), name='experiments-start'),
    path('experiments/<int:experiment_id>/select-model/', ExperimentSelectModelView.as_view(), name='experiments-select-model'),
    path('experiments/<int:experiment_id>/set-hyperparameters/', ExperimentSetHyperparametersView.as_view(), name='experiments-set-hyperparameters'),
    path('experiments/<int:experiment_id>/train/', ExperimentTrainView.as_view(), name='experiments-train'),
    path('experiments/<int:experiment_id>/', ExperimentDetailView.as_view(), name='experiments-detail'),

    # Frontend compatibility (current UI calls these)
    path('options/', PlaygroundCompatOptionsView.as_view(), name='options'),
    path('jobs/', PlaygroundCompatJobsView.as_view(), name='jobs'),
    path('jobs/<int:experiment_id>/', PlaygroundCompatJobDetailView.as_view(), name='job-detail'),
    path('jobs/<int:experiment_id>/status/', PlaygroundCompatJobStatusView.as_view(), name='job-status'),
    path('jobs/<int:experiment_id>/metrics/', PlaygroundCompatJobMetricsView.as_view(), name='job-metrics'),
]
