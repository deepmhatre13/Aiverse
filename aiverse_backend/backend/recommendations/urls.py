from django.urls import path
from . import views

urlpatterns = [
    path('', views.RecommendationListView.as_view(), name='recommendation-list'),
    path('personalised/', views.PersonalisedRecommendationsView.as_view(), name='recommendation-personalised'),
    path('dkt-mastery/', views.DKTMasteryView.as_view(), name='dkt-mastery'),
    path('irt-ability/', views.IRTAbilityView.as_view(), name='irt-ability'),
    path('after-problem/<slug:slug>/', views.ProblemNextRecommendationsView.as_view(), name='after-problem'),
    path('<int:rec_id>/dismiss/', views.DismissRecommendationView.as_view(), name='dismiss-recommendation'),
]
