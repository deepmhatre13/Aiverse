from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from intelligence.models import ExperimentRun, SuggestionLog, UserActivity, UserProfile
from intelligence.serializers import (
    ExperimentRunSerializer,
    SuggestionLogSerializer,
    UserActivitySerializer,
    UserProfileSerializer,
)
from intelligence.services.suggestion_engine import generate_suggestions
from utils.cache import cache_get_or_set


def envelope(success: bool, data=None, error=None, http_status=status.HTTP_200_OK):
    payload = {
        "success": success,
        "data": data if success else None,
        "error": None if success else error,
    }
    return Response(payload, status=http_status)


def _safe_error_message(exc: Exception) -> str:
    if getattr(settings, "DEBUG", False):
        return str(exc)
    return "An unexpected error occurred."


def _profile_cache_key(user_id) -> str:
    return f"intelligence:profile:{user_id}"


class IntelligenceProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            def compute():
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                serialized = UserProfileSerializer(profile).data
                return {
                    "skill_level": serialized.get("skill_level"),
                    "avg_score": float(serialized.get("avg_score") or 0.0),
                    "total_runs": int(serialized.get("total_runs") or 0),
                    "strengths": serialized.get("strengths") or [],
                    "weaknesses": serialized.get("weaknesses") or [],
                    "preferred_models": serialized.get("preferred_models") or [],
                }

            payload = cache_get_or_set(_profile_cache_key(request.user.pk), compute, ttl=300)
            return envelope(True, payload)
        except Exception as exc:
            return envelope(
                False,
                error=_safe_error_message(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IntelligenceSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            generate_suggestions(request.user)
            logs = SuggestionLog.objects.filter(user=request.user).order_by("-created_at")[:5]
            return envelope(True, {"suggestions": SuggestionLogSerializer(logs, many=True).data})
        except Exception as exc:
            return envelope(
                False,
                error=_safe_error_message(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IntelligenceHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            runs = ExperimentRun.objects.filter(user=request.user).order_by("-created_at")[:20]
            return envelope(True, {"history": ExperimentRunSerializer(runs, many=True).data})
        except Exception as exc:
            return envelope(
                False,
                error=_safe_error_message(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class IntelligenceActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            activities = UserActivity.objects.filter(user=request.user).order_by("-created_at")[:20]
            return envelope(True, {"activity": UserActivitySerializer(activities, many=True).data})
        except Exception as exc:
            return envelope(
                False,
                error=_safe_error_message(exc),
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

