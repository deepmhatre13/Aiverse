from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProblemListView.as_view(), name='problem-list'),
    path('<slug:slug>/', views.ProblemDetailView.as_view(), name='problem-detail'),
]
