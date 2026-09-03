from django.conf import settings
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from submissions.models import Submission
from .models import Problem
from .serializers import ProblemListSerializer, ProblemDetailSerializer
from utils.cache import (
    cache_get,
    cache_set,
    problems_list_cache_key,
    CacheTTL,
)


class ProblemListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProblemListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'tags']
    ordering_fields = ['created_at', 'solve_count', 'points', 'order_index']
    ordering = ['order_index']

    def list(self, request, *args, **kwargs):
        # Cache only the default listing (no filters/search/sort) for 5 minutes.
        if request.query_params:
            return super().list(request, *args, **kwargs)

        key = problems_list_cache_key()
        cached = cache_get(key)
        if cached is not None:
            from rest_framework.response import Response
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        cache_set(key, response.data, ttl=CacheTTL.PROBLEMS_LIST)
        return response

    def get_queryset(self):
        qs = Problem.objects.filter(is_active=True)
        difficulty = self.request.query_params.get('difficulty')
        category = self.request.query_params.get('category')
        if difficulty and difficulty != 'All':
            qs = qs.filter(difficulty=difficulty)
        if category and category != 'All':
            qs = qs.filter(category=category)
        return qs


class ProblemDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProblemDetailSerializer
    queryset = Problem.objects.filter(is_active=True)
    lookup_field = 'slug'


class ProblemResponsesInternalView(APIView):
    def get(self, request):
        service_key = request.headers.get("X-Service-Key")
        if service_key != settings.ML_INTERNAL_KEY:
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        try:
            limit = min(int(request.query_params.get("limit", 10000)), 10000)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except ValueError:
            return Response(
                {"detail": "limit and offset must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submissions = Submission.objects.select_related("problem", "user").order_by("submitted_at")[offset: offset + limit]
        results = [
            {
                "user_id": submission.user_id,
                "problem_id": str(submission.problem_id),
                "concept_tag": getattr(submission.problem, "concept_tag", "") or "",
                "correct": submission.status == "accepted",
                "timestamp": submission.submitted_at.isoformat(),
            }
            for submission in submissions
        ]
        return Response(results, status=status.HTTP_200_OK)
