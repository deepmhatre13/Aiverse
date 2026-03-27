from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import GoogleLoginView
from users.views import ProfileView, ProfileUpdateView, GitHubConnectView, GitHubDisconnectView, LinkedInConnectView, LinkedInDisconnectView
from backend.health import HealthCheckView
from dashboard.views import PerformanceView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckView.as_view(), name='health-check'),
    path('api/auth/google/', GoogleLoginView.as_view(), name='google-login'),
    # User API endpoints
    path('api/users/', include('users.urls')),
    path('api/ml/', include('ml.urls')),
    path('api/learn/', include('learn.urls')),
    path('api/mentor/', include('mentor.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/performance/', PerformanceView.as_view(), name='performance'),
    path('api/profile/', ProfileView.as_view(), name='profile'),
    path('api/profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('api/profile/github/connect/', GitHubConnectView.as_view(), name='github-connect'),
    path('api/profile/github/disconnect/', GitHubDisconnectView.as_view(), name='github-disconnect'),
    path('api/profile/linkedin/connect/', LinkedInConnectView.as_view(), name='linkedin-connect'),
    path('api/profile/linkedin/disconnect/', LinkedInDisconnectView.as_view(), name='linkedin-disconnect'),
    path('api/timeline/', include('timeline.urls')),
    path('api/tracks/', include('tracks.urls')),
    path('api/leaderboard/', include('leaderboard.urls')),
    path('api/discussions/', include('discussions.urls')),
    path('api/playground/', include('playground.urls')),
    path('api/live/', include('live.urls')),
    path('api/problems/', include('problems.urls')),
    path('api/submissions/', include('submissions.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)