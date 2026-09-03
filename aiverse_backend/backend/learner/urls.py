"""
URL routes for learner app.
"""

from django.urls import path
from .views import (
    LearningPathView,
    KnowledgeGapView,
    KnowledgeGapWidgetView,
    ConceptMasteryListView,
    TopicAnalysisView,
    WeakTopicWidgetView,
    LearnerProfileView,
    MasteryHistoryView,
    PrerequisiteView,
)

urlpatterns = [
    path('learning-path/', LearningPathView.as_view(), name='learning-path'),
    path('knowledge-gaps/', KnowledgeGapView.as_view(), name='knowledge-gaps'),
    path('widgets/knowledge-gaps/', KnowledgeGapWidgetView.as_view(), name='widget-knowledge-gaps'),
    path('widgets/weak-topics/', WeakTopicWidgetView.as_view(), name='widget-weak-topics'),
    path('concept-mastery/', ConceptMasteryListView.as_view(), name='concept-mastery-list'),
    path('topic-analysis/', TopicAnalysisView.as_view(), name='topic-analysis'),
    # Frontend-contract endpoints (reuse existing serializers/services)
    path('profile/', LearnerProfileView.as_view(), name='learner-profile'),
    path('mastery/', ConceptMasteryListView.as_view(), name='learner-mastery'),
    path('mastery-history/', MasteryHistoryView.as_view(), name='learner-mastery-history'),
    path('prerequisites/', PrerequisiteView.as_view(), name='learner-prerequisites'),
]
