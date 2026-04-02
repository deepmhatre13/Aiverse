from django.urls import path

from intelligence import views


urlpatterns = [
    path("profile/", views.IntelligenceProfileView.as_view(), name="intelligence-profile"),
    path("suggestions/", views.IntelligenceSuggestionsView.as_view(), name="intelligence-suggestions"),
    path("history/", views.IntelligenceHistoryView.as_view(), name="intelligence-history"),
    path("activity/", views.IntelligenceActivityView.as_view(), name="intelligence-activity"),
]

