"""Internal APIs for ML service training — shared-secret auth only."""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from learn.models import CodingProblem, Lesson
from tracking.models import LearnerEvent


def _check_internal_key(request):
    key = request.headers.get("X-Service-Key") or request.META.get("HTTP_X_SERVICE_KEY")
    expected = getattr(settings, "ML_INTERNAL_KEY", "aiverse_ml_internal_key")
    return key == expected


def _lesson_completion_rate(lesson_id: int) -> float:
    opened = LearnerEvent.objects.filter(
        content_type="lesson", content_id=lesson_id, event_type="LESSON_OPENED"
    ).count()
    completed = LearnerEvent.objects.filter(
        content_type="lesson", content_id=lesson_id, event_type="LESSON_COMPLETED"
    ).count()
    if opened == 0:
        return 0.5
    return round(completed / opened, 3)


class InternalLessonsCatalogueView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not _check_internal_key(request):
            return Response({"error": "forbidden"}, status=403)

        lessons = Lesson.objects.filter(is_active=True).select_related("course")
        data = []
        for l in lessons:
            prereq_concepts = list(
                l.prerequisites.filter(is_active=True).values_list("concept_tag", flat=True)
            )
            prereq_concepts = [c for c in prereq_concepts if c]
            data.append({
                "id": l.id,
                "title": l.title,
                "description": l.description or "",
                "concept_tag": l.concept_tag or "",
                "difficulty": l.difficulty or "beginner",
                "tags": l.tags or [],
                "learning_objectives": l.learning_objectives or [],
                "course_id": l.course_id,
                "duration_minutes": l.duration_minutes,
                "completion_rate": _lesson_completion_rate(l.id),
                "prerequisite_concept_tags": prereq_concepts,
            })
        return Response(data)


class InternalEventsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not _check_internal_key(request):
            return Response({"error": "forbidden"}, status=403)

        since = timezone.now() - timedelta(days=365)
        events = LearnerEvent.objects.filter(
            timestamp__gte=since,
            content_type="lesson",
        ).values("user_id", "content_id", "event_type", "timestamp")[:50000]

        rows = []
        for e in events:
            rows.append({
                "user_id": e["user_id"],
                "lesson_id": e["content_id"],
                "event_type": e["event_type"],
                "timestamp": e["timestamp"].isoformat(),
            })
        return Response(rows)


class InternalProblemsCatalogueView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not _check_internal_key(request):
            return Response({"error": "forbidden"}, status=403)

        problems = CodingProblem.objects.filter(is_active=True).order_by("order")
        data = [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "concept_tag": p.concept_tag,
                "difficulty": p.difficulty,
                "points": p.points,
            }
            for p in problems
        ]
        return Response(data)


class InternalProblemResponsesView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        if not _check_internal_key(request):
            return Response({"error": "Forbidden"}, status=403)

        events = LearnerEvent.objects.filter(
            event_type__in=["CODE_PASSED", "CODE_FAILED", "PROBLEM_SOLVED"],
            content_type="problem",
            content_id__isnull=False,
        ).select_related("user").order_by("-timestamp")[:10000]

        data = [
            {
                "user_id": e.user_id,
                "problem_id": e.content_id,
                "concept_tag": (e.metadata or {}).get("concept_tag", ""),
                "correct": e.event_type in ("CODE_PASSED", "PROBLEM_SOLVED"),
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]
        return Response(data)
