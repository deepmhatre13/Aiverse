from rest_framework import status as http_status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate
from django.db.models import Count
from datetime import date, timedelta

from problems.models import Problem
from .models import Submission
from .serializers import SubmissionSerializer, SubmitSerializer, RunSerializer
from .grader import grade_submission, run_sample
from utils.cache import cache_set, submission_cache_key, CacheTTL

User = get_user_model()


class SubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            problem = Problem.objects.get(slug=data['problem_slug'], is_active=True)
        except Problem.DoesNotExist:
            return Response({'error': 'Problem not found'}, status=404)

        # Grade synchronously (for small test suites)
        result = grade_submission(
            data['code'], data['language'],
            problem.test_cases, problem.points
        )

        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=data['code'],
            language=data['language'],
            status=result['status'],
            score=result['score'],
            max_score=result['max_score'],
            execution_time_ms=result['execution_time_ms'],
            test_results=result['test_results'],
            error_message=result['error_message'],
        )

        payload = {
            'submission_id': str(submission.id),
            'status': submission.status,
            'score': float(submission.score),
            'max_score': float(submission.max_score),
            'test_results': submission.test_results,
            'execution_time_ms': submission.execution_time_ms,
            'error_message': submission.error_message,
        }

        cache_set(submission_cache_key(submission.id), payload, ttl=CacheTTL.SUBMISSION)
        return Response(payload, status=http_status.HTTP_201_CREATED)


class RunView(APIView):
    """Run code against public test cases only — no submission saved."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            problem = Problem.objects.get(slug=data['problem_slug'])
        except Problem.DoesNotExist:
            return Response({'error': 'Problem not found'}, status=404)

        result = run_sample(data['code'], data['language'], problem.test_cases)
        return Response(result)


class RecentSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 10)), 50)
        subs = Submission.objects.filter(
            user=request.user
        ).select_related('problem').order_by('-submitted_at')[:limit]
        return Response(SubmissionSerializer(subs, many=True).data)


class HeatmapView(APIView):
    """Returns { date_str: count } for contribution heatmap (last 365 days)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        end = date.today()
        start = end - timedelta(days=365)

        counts = (
            Submission.objects
            .filter(user=request.user, submitted_at__date__gte=start)
            .annotate(day=TruncDate('submitted_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )

        heatmap = {str(row['day']): row['count'] for row in counts}
        return Response({
            'heatmap': heatmap,
            'total': sum(heatmap.values()),
        })
