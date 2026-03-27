from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # Profile
    path('me/', views.MeView.as_view(), name='profile-me'),
    path('<int:user_id>/', views.PublicProfileView.as_view(), name='profile-public'),
    path('u/<str:username>/', views.PublicProfileByUsernameView.as_view(), name='profile-by-username'),
]