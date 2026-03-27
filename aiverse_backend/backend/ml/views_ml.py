"""
ML Problem evaluation and submission API endpoints.

Two-step flow:
1. POST /api/ml/problems/{slug}/evaluate/ - Stateless evaluation
2. POST /api/ml/problems/{slug}/submit/ - Stateful submission + leaderboard
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models_ml import Problem, Submission, Leaderboard
from .serializers_ml import (
    ProblemSerializer,
    EvaluationRequestSerializer,
    EvaluationResponseSerializer,
    EvaluationErrorSerializer,
    SubmissionRequestSerializer,
    SubmissionSerializer,
    LeaderboardEntrySerializer,
)
from .evaluation_service import evaluate_code
from .leaderboard_service import (
    update_leaderboard_entry,
    get_leaderboard,
    get_leaderboard_position,
    mark_best_submission,
)


class ProblemDetailView(APIView):
    """Get problem details."""
    
    def get(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        serializer = ProblemSerializer(problem)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EvaluateView(APIView):
    """
    Evaluate code against a problem (stateless).
    
    POST /api/ml/problems/{slug}/evaluate/
    
    Request:
    {
        "code": "...",
        "metric": "accuracy"  # optional
    }
    
    Response (Success):
    {
        "status": "success",
        "metric": "accuracy",
        "score": 0.87,
        "threshold": 0.8,
        "meets_threshold": true
    }
    
    Response (Error):
    {
        "status": "error",
        "error_type": "VALIDATION_ERROR",
        "message": "..."
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        # Validate request
        serializer = EvaluationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "error_type": "REQUEST_ERROR",
                "message": str(serializer.errors)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        code = serializer.validated_data['code']
        metric = serializer.validated_data.get('metric')
        
        # Check problem exists
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        
        # Evaluate code
        result = evaluate_code(slug, code, metric)
        
        # Return appropriate response
        if result['status'] == 'success':
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_200_OK)  # 200 even for errors (expected)


class SubmitView(APIView):
    """
    Submit code to leaderboard (stateful).
    
    POST /api/ml/problems/{slug}/submit/
    
    Request:
    {
        "code": "...",
        "metric": "accuracy"
    }
    
    Response (Accepted):
    {
        "status": "success",
        "score": 0.87,
        "metric": "accuracy",
        "rank": 12
    }
    
    Response (Rejected - Below Threshold):
    {
        "status": "rejected",
        "score": 0.63,
        "reason": "Score below submission threshold (0.8)"
    }
    
    Response (Error):
    {
        "status": "error",
        "error_type": "...",
        "message": "..."
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        # Validate request
        serializer = SubmissionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": "error",
                "error_type": "REQUEST_ERROR",
                "message": str(serializer.errors)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        code = serializer.validated_data['code']
        metric = serializer.validated_data.get('metric')
        
        # Check problem exists
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        
        # Re-evaluate code (never trust frontend)
        result = evaluate_code(slug, code, metric)
        
        # If evaluation failed, reject submission
        if result['status'] == 'error':
            submission = Submission.objects.create(
                user=request.user,
                problem=problem,
                code=code,
                metric=metric or problem.default_metric,
                status='error',
                error_type=result['error_type'],
                error_message=result['message']
            )
            
            return Response({
                "status": "error",
                "error_type": result['error_type'],
                "message": result['message']
            }, status=status.HTTP_200_OK)
        
        # Check threshold
        score = result['score']
        threshold = result['threshold']
        meets_threshold = result['meets_threshold']
        eval_metric = result['metric']
        
        # Create submission record
        if meets_threshold:
            submission_status = 'passed'
        else:
            submission_status = 'rejected'
        
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=code,
            metric=eval_metric,
            public_score=score,
            private_score=score,
            status=submission_status
        )
        
        # If accepted, update leaderboard
        if meets_threshold:
            leaderboard_entry = update_leaderboard_entry(request.user, problem, submission)
            mark_best_submission(request.user, problem, submission)
            
            return Response({
                "status": "accepted",
                "score": score,
                "metric": eval_metric,
                "rank": leaderboard_entry.rank
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "rejected",
                "score": score,
                "reason": f"Score {score} below submission threshold ({threshold})"
            }, status=status.HTTP_200_OK)


class LeaderboardView(APIView):
    """Get leaderboard for a problem."""
    
    def get(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        
        # Get limit from query param
        limit = int(request.query_params.get('limit', 100))
        
        entries = get_leaderboard(problem, limit=limit)
        serializer = LeaderboardEntrySerializer(entries, many=True)
        
        return Response({
            "problem": problem.slug,
            "total": Leaderboard.objects.filter(problem=problem).count(),
            "entries": serializer.data
        }, status=status.HTTP_200_OK)


class UserRankView(APIView):
    """Get user's rank on a problem."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        
        position = get_leaderboard_position(request.user, problem)
        
        if not position:
            return Response({
                "message": "User has no submissions on this problem"
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(position, status=status.HTTP_200_OK)


class SubmissionHistoryView(APIView):
    """Get user's submission history for a problem."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        problem = get_object_or_404(Problem, slug=slug, is_active=True)
        
        submissions = Submission.objects.filter(
            user=request.user,
            problem=problem
        ).order_by('-created_at')
        
        serializer = SubmissionSerializer(submissions, many=True)
        
        return Response({
            "problem": problem.slug,
            "count": submissions.count(),
            "submissions": serializer.data
        }, status=status.HTTP_200_OK)
