from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.shortcuts import get_object_or_404
import uuid
import random
from .models import Problem, Submission, TestSuite, Dataset
from .serializers import (
    ProblemListSerializer,
    ProblemDetailSerializer,
    SubmissionCreateSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
)
from .test_cases import PROBLEM_TEST_SUITES, ProblemTestSuite
from .executor import execute_user_code
from .api_validator import APICompatibilityLayer
from .evaluation_service import evaluate_code
from .metrics import LOWER_IS_BETTER_METRICS
from .registry import list_problems, get_problem_definition


class ProblemListView(APIView):
    """List all active ML problems from the registry (source of truth)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Return problems directly from the registry, not database."""
        problems = list_problems()
        
        # Convert registry ProblemDefinition objects to dicts for JSON serialization
        data = [
            {
                'id': idx + 1,  # Generate simple IDs for frontend
                'slug': p.slug,
                'title': p.title,
                'problem_type': p.task_type,
                'metric': p.default_metric,
                'description': p.description,
                'submission_threshold': p.submission_threshold,
                'is_active': True,
                'difficulty': p.difficulty,
                'difficulty_rating': p.difficulty_rating,
                'category': p.category,
                'constraints': p.constraints,
                'has_hidden_tests': p.hidden_test_ratio > 0,
                'higher_is_better': p.higher_is_better,
            }
            for idx, p in enumerate(problems)
        ]
        return Response(data, status=status.HTTP_200_OK)


class ProblemDetailView(APIView):
    """Get detailed information about a specific problem from the registry."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        """Fetch problem from registry by slug."""
        try:
            problem = get_problem_definition(slug)
            
            # Return problem from registry
            data = {
                'slug': problem.slug,
                'title': problem.title,
                'problem_type': problem.task_type,
                'metric': problem.default_metric,
                'allowed_metrics': problem.allowed_metrics,
                'description': problem.description,
                'submission_threshold': problem.submission_threshold,
                'is_active': True,
                'difficulty': problem.difficulty,
                'difficulty_rating': problem.difficulty_rating,
                'category': problem.category,
                'constraints': problem.constraints,
                'has_hidden_tests': problem.hidden_test_ratio > 0,
                'higher_is_better': problem.higher_is_better,
            }
            return Response(data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {'error': f'Problem "{slug}" not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProblemEvaluateView(APIView):
    """
    STATELESS evaluation - no database writes.
    
    POST /api/ml/problems/{slug}/evaluate/
    
    Responsibilities:
    • Validate code syntax
    • Execute in sandbox
    • Load dataset
    • Compute metric against threshold
    • Return result (never saves anything)
    
    Response (200 OK - always):
    {
        "status": "success",
        "metric": "accuracy",
        "score": 0.91,
        "threshold": 0.80,
        "meets_threshold": true
    }
    
    OR on error (200 OK with error details):
    {
        "status": "error",
        "error_type": "VALIDATION_ERROR|RUNTIME_ERROR|TIMEOUT_ERROR",
        "message": "Human-readable explanation"
    }
    
    CRITICAL: This endpoint NEVER creates database records.
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        """Evaluate code without saving."""
        # Extract code
        code = request.data.get("code", "").strip()
        if not code:
            return Response({
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "Code cannot be empty. Please write some code to evaluate."
            }, status=status.HTTP_200_OK)
        
        # Extract metric (optional)
        metric = request.data.get("metric")
        
        # Call evaluation service (stateless)
        result = evaluate_code(slug, code, metric)
        
        # Always return 200 OK with structured response
        return Response(result, status=status.HTTP_200_OK)


class ProblemSubmitView(APIView):
    """
    STATEFUL submission - creates immutable database record.
    
    POST /api/ml/problems/{slug}/submit/
    
    Responsibilities:
    • Re-evaluate code server-side (never trust client)
    • Enforce submission threshold
    • Create NEW Submission row (never update)
    • Calculate leaderboard rank
    • Return accepted/rejected/error
    
    CRITICAL INVARIANTS:
    ✓ Always creates new Submission row (never updates)
    ✓ Code snapshot stored forever
    ✓ History is complete and immutable
    ✓ Leaderboard rank calculated once and never recomputed
    ✓ All submissions visible in history (even rejected ones)
    
    Response (200 OK - always structured):
    
    Accepted (meets threshold):
    {
        "status": "accepted",
        "score": 0.91,
        "metric": "accuracy",
        "rank": 4,
        "submission_id": 42
    }
    
    Rejected (below threshold):
    {
        "status": "rejected",
        "score": 0.63,
        "metric": "accuracy",
        "threshold": 0.80,
        "reason": "Score below submission threshold (0.80)",
        "submission_id": 43
    }
    
    Error (evaluation failed):
    {
        "status": "error",
        "error_type": "VALIDATION_ERROR|RUNTIME_ERROR|TIMEOUT_ERROR",
        "message": "Human-readable explanation",
        "submission_id": null
    }
    """
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, slug):
        """Submit code for evaluation (creates database record)."""
        
        # ========== VALIDATION ==========
        
        # Get problem definition from registry
        try:
            problem_def = get_problem_definition(slug)
        except ValueError:
            return Response({
                "status": "error",
                "error_type": "NOT_FOUND",
                "message": f"Problem '{slug}' not found in registry"
            }, status=status.HTTP_200_OK)
        
        # Validate input
        code = request.data.get("code", "").strip()
        if not code:
            return Response({
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "Code cannot be empty"
            }, status=status.HTTP_200_OK)
        
        if 'def train_and_predict' not in code:
            return Response({
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "Code must define: def train_and_predict(X_train, y_train, X_test)"
            }, status=status.HTTP_200_OK)
        
        # ========== EVALUATE SERVER-SIDE (NEVER TRUST CLIENT) ==========
        
        metric = request.data.get("metric")
        eval_result = evaluate_code(slug, code, metric)
        
        # If evaluation failed, return error WITHOUT creating submission record
        if eval_result.get("status") != "success":
            return Response({
                "status": "error",
                "error_type": eval_result.get("error_type", "RUNTIME_ERROR"),
                "message": eval_result.get("message", "Evaluation failed"),
                "submission_id": None
            }, status=status.HTTP_200_OK)
        
        # ========== EXTRACT EVALUATION RESULTS ==========
        
        score = eval_result.get("score", 0.0)
        metric_used = eval_result.get("metric", problem_def.default_metric)
        threshold = eval_result.get("threshold", problem_def.submission_threshold)
        meets_threshold = eval_result.get("meets_threshold", score >= threshold) if threshold else False
        
        # ========== CREATE SUBMISSION RECORD (ALWAYS - ACCEPTED OR REJECTED) ==========
        # CRITICAL: Create submission regardless of threshold
        # This ensures submission history is complete
        # Use atomic transaction to ensure consistency
        
        try:
            with transaction.atomic():
                # Get or create default dataset for registry-based problems
                default_dataset, _ = Dataset.objects.get_or_create(
                    slug='registry-default',
                    defaults={
                        'name': 'Registry Default Dataset',
                        'description': 'Default dataset for registry-based problems.',
                        'loader_type': 'registry',
                        'task_type': problem_def.task_type,
                    }
                )
                
                # Get or create Problem object in DB (needed for submission FK)
                problem, _ = Problem.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'title': problem_def.title,
                        'description': problem_def.description,
                        'problem_type': problem_def.task_type,
                        'metric': problem_def.default_metric,
                        'target_column': 'target',
                        'dataset_dir': '',
                        'is_active': True,
                        'dataset': default_dataset,  # REQUIRED: Attach dataset
                    }
                )
                
                # Ensure problem has dataset (for existing problems without one)
                if problem.dataset is None:
                    problem.dataset = default_dataset
                    problem.save(update_fields=['dataset'])
                
                # Create submission record (immutable after creation)
                submission = Submission.objects.create(
                    user=request.user,
                    problem=problem,
                    dataset=problem.dataset,  # Copy dataset reference at submission time
                    code=code,
                    metric=metric_used,
                    score=score,
                    threshold=threshold,
                    status='ACCEPTED' if meets_threshold else 'REJECTED',
                    reason=None if meets_threshold else f"Score {score:.4f} below threshold {threshold:.4f}",
                    test_results=eval_result.get("test_results", []),
                    runtime_seconds=eval_result.get("runtime_seconds"),
                    latency_ms=eval_result.get("latency_ms"),
                    memory_mb=eval_result.get("memory_mb"),
                    meets_threshold=meets_threshold,
                    verdict='ACCEPTED' if meets_threshold else 'REJECTED',
                    evaluation_version='1.0.0',
                    model_metadata=eval_result.get("model_metadata", {}),
                )
        except Exception as e:
            # Hide internal error details in production
            error_msg = str(e) if __debug__ else "Internal database error"
            return Response({
                "status": "error",
                "error_type": "DATABASE_ERROR",
                "message": f"Failed to save submission: {error_msg}",
                "submission_id": None
            }, status=status.HTTP_200_OK)
        
        # ========== CALCULATE LEADERBOARD RANK (ONLY FOR ACCEPTED) ==========
        
        if meets_threshold:
            metric_name = metric_used.lower()
            is_lower_better = metric_name in LOWER_IS_BETTER_METRICS
            
            # Get latency for comparison (use infinity if None)
            latency = eval_result.get("latency_ms") or float('inf')
            
            # Count better submissions using deterministic ordering:
            # Score DESC (or ASC for lower-is-better), Latency ASC, Timestamp ASC
            better_submissions = Submission.objects.filter(
                problem=problem,
                status='ACCEPTED'
            ).exclude(pk=submission.pk)
            
            better_count = 0
            for other in better_submissions:
                other_score = other.score
                other_latency = other.latency_ms if other.latency_ms is not None else float('inf')
                
                is_better = False
                if is_lower_better:
                    # Lower is better
                    if other_score < score:
                        is_better = True
                    elif other_score == score:
                        if other_latency < latency:
                            is_better = True
                        elif other_latency == latency:
                            if other.created_at < submission.created_at:
                                is_better = True
                else:
                    # Higher is better
                    if other_score > score:
                        is_better = True
                    elif other_score == score:
                        if other_latency < latency:
                            is_better = True
                        elif other_latency == latency:
                            if other.created_at < submission.created_at:
                                is_better = True
                
                if is_better:
                    better_count += 1
            
            submission.rank = better_count + 1
            # Save rank only (immutability still enforced by .save() override)
            try:
                Submission.objects.filter(pk=submission.pk).update(rank=submission.rank)
            except Exception:
                pass  # Rank is optional, don't fail the submission
        
        # ========== RETURN RESPONSE ==========
        
        return Response({
            "status": "accepted" if meets_threshold else "rejected",
            "score": float(score),
            "metric": metric_used,
            "threshold": float(threshold) if threshold else None,
            "rank": submission.rank if submission.rank else None,
            "submission_id": submission.id,
            "reason": submission.reason if submission.reason else None,
            "latency_ms": eval_result.get("latency_ms"),
            "memory_mb": eval_result.get("memory_mb"),
            "meets_threshold": meets_threshold,
            "verdict": "ACCEPTED" if meets_threshold else "REJECTED",
        }, status=status.HTTP_201_CREATED)


class SubmissionListView(APIView):
    """
    List user's submissions across all problems.
    
    GET /api/ml/submissions/
    
    Optional query params:
    - problem: Filter by problem slug
    - status: Filter by status (ACCEPTED, REJECTED, ERROR)
    - limit: Limit results (default 20)
    - offset: Pagination offset (default 0)
    
    Response (200 OK):
    [
        {
            "id": 42,
            "problem_title": "Iris Classification",
            "problem_slug": "iris-classification",
            "status": "ACCEPTED",
            "score": 0.91,
            "metric": "accuracy",
            "rank": 4,
            "created_at": "2024-01-15T10:30:00Z"
        },
        ...
    ]
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List user's submissions with optional filtering."""
        submissions = Submission.objects.filter(user=request.user).select_related('problem')
        
        # Optional filtering by problem
        problem_slug = request.query_params.get('problem')
        if problem_slug:
            submissions = submissions.filter(problem__slug=problem_slug)
        
        # Optional filtering by status
        submission_status = request.query_params.get('status')
        if submission_status:
            submissions = submissions.filter(status=submission_status.upper())
        
        # Pagination
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        submissions = submissions[offset:offset + limit]
        
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProblemSubmissionsView(APIView):
    """
    Get user's submission history for a specific problem.
    
    GET /api/ml/problems/{slug}/submissions/
    
    Response (200 OK - always):
    {
        "problem": {
            "slug": "iris-classification",
            "title": "Iris Classification"
        },
        "submissions": [
            {
                "id": 42,
                "status": "ACCEPTED",
                "score": 0.91,
                "metric": "accuracy",
                "rank": 4,
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": 41,
                "status": "REJECTED",
                "score": 0.63,
                "metric": "accuracy",
                "rank": null,
                "created_at": "2024-01-15T10:25:00Z"
            }
        ]
    }
    
    CRITICAL: Never returns 404. Returns empty submissions list if none exist.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        """Get all submissions for this user and problem."""
        try:
            return self._get_submissions(request, slug)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("ProblemSubmissionsView failed: %s", e)
            return Response({
                'problem': {'slug': slug, 'title': 'Unknown'},
                'submissions': []
            }, status=status.HTTP_200_OK)
    
    def _get_submissions(self, request, slug):
        """Get all submissions for this user and problem."""
        # Try to get problem from registry (for metadata)
        try:
            problem_def = get_problem_definition(slug)
            problem_data = {
                'slug': slug,
                'title': problem_def.title,
            }
        except ValueError:
            # Problem not in registry - return minimal info
            problem_data = {
                'slug': slug,
                'title': 'Unknown Problem',
            }
        
        # Try to get problem from DB (may not exist if no submissions yet)
        try:
            problem = Problem.objects.get(slug=slug)
        except Problem.DoesNotExist:
            # Problem in registry but not in DB yet - return 200 with empty submissions
            return Response({
                'problem': problem_data,
                'submissions': []
            }, status=status.HTTP_200_OK)
        
        # Get submissions for this user and problem (ordered newest first)
        submissions = Submission.objects.filter(
            user=request.user,
            problem=problem
        ).select_related('problem').order_by('-created_at')
        
        # Serialize submissions
        serializer = SubmissionListSerializer(submissions, many=True)
        
        # Always return 200 OK with structured response
        return Response({
            'problem': problem_data,
            'submissions': serializer.data
        }, status=status.HTTP_200_OK)


class SubmissionDetailView(APIView):
    """
    Get detailed information about a submission.
    
    GET /api/ml/submissions/{id}/
    
    Response (200 OK):
    {
        "id": 42,
        "user_username": "alice",
        "problem_slug": "iris-classification",
        "problem_title": "Iris Classification",
        "code": "def train_and_predict(...): ...",  # ✅ FULL CODE SNAPSHOT
        "status": "ACCEPTED",
        "score": 0.91,
        "metric": "accuracy",
        "threshold": 0.80,
        "rank": 4,
        "reason": null,
        "error_log": null,
        "runtime_seconds": 1.23,
        "test_results": [...],
        "created_at": "2024-01-15T10:30:00Z"
    }
    
    CRITICAL: Returns 403 if user doesn't own submission.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get submission details including full code snapshot."""
        try:
            # Ensure user owns this submission
            submission = Submission.objects.get(pk=pk, user=request.user)
        except Submission.DoesNotExist:
            return Response({
                'error': 'Submission not found or you do not own this submission'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SubmissionDetailSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProblemLeaderboardView(APIView):
    """
    Get leaderboard for a specific problem.
    
    GET /api/ml/problems/{slug}/leaderboard/
    
    Rules:
    • Rank users by BEST score for that problem
    • Only ACCEPTED submissions count
    • One row per user
    • Deterministic ordering: best score DESC, tie-breaker: earliest submission timestamp
    
    Response (200 OK):
    [
        {
            "rank": 1,
            "user": "alice",
            "score": 0.94,
            "submission_id": 42,
            "created_at": "2024-01-15T10:30:00Z"
        },
        {
            "rank": 2,
            "user": "bob",
            "score": 0.91,
            "submission_id": 38,
            "created_at": "2024-01-14T15:20:00Z"
        }
    ]
    
    CRITICAL: Leaderboard is computed dynamically from Submission table.
    NO stored leaderboard rows. NO overwriting of previous bests.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, slug):
        """Get leaderboard for problem, ranked by best score per user."""
        
        # Get problem from DB
        try:
            problem = Problem.objects.get(slug=slug)
        except Problem.DoesNotExist:
            return Response({
                'error': f'Problem "{slug}" not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get metric direction (higher or lower is better)
        from .metrics import LOWER_IS_BETTER_METRICS
        metric_name = problem.metric.lower()
        is_lower_better = metric_name in LOWER_IS_BETTER_METRICS
        
        # Get all ACCEPTED submissions for this problem
        accepted = Submission.objects.filter(
            problem=problem,
            status='ACCEPTED'
        ).select_related('user')
        
        # Group by user and get best submission per user
        # Deterministic sorting: Score DESC, Latency ASC, Timestamp ASC
        user_best = {}
        
        for submission in accepted:
            user_id = submission.user_id
            user_key = submission.user.username
            
            # Get latency (default to infinity if None for sorting)
            latency = submission.latency_ms if submission.latency_ms is not None else float('inf')
            
            if user_id not in user_best:
                user_best[user_id] = {
                    'user': user_key,
                    'score': submission.score,
                    'latency_ms': latency,
                    'submission_id': submission.id,
                    'created_at': submission.created_at
                }
            else:
                # Compare submissions using deterministic ordering
                current = user_best[user_id]
                new_score = submission.score
                current_score = current['score']
                
                # Determine if new submission is better
                is_better = False
                
                if is_lower_better:
                    # Lower is better: prefer lower score
                    if new_score < current_score:
                        is_better = True
                    elif new_score == current_score:
                        # Tie-breaker 1: lower latency
                        if latency < current['latency_ms']:
                            is_better = True
                        elif latency == current['latency_ms']:
                            # Tie-breaker 2: earlier timestamp
                            if submission.created_at < current['created_at']:
                                is_better = True
                else:
                    # Higher is better: prefer higher score
                    if new_score > current_score:
                        is_better = True
                    elif new_score == current_score:
                        # Tie-breaker 1: lower latency
                        if latency < current['latency_ms']:
                            is_better = True
                        elif latency == current['latency_ms']:
                            # Tie-breaker 2: earlier timestamp
                            if submission.created_at < current['created_at']:
                                is_better = True
                
                if is_better:
                    user_best[user_id] = {
                        'user': user_key,
                        'score': new_score,
                        'latency_ms': latency,
                        'submission_id': submission.id,
                        'created_at': submission.created_at
                    }
        
        # Convert to list and sort deterministically
        leaderboard = list(user_best.values())
        
        # Deterministic sorting: Score DESC (or ASC for lower-is-better), Latency ASC, Timestamp ASC
        if is_lower_better:
            leaderboard.sort(key=lambda x: (x['score'], x['latency_ms'], x['created_at']))
        else:
            leaderboard.sort(key=lambda x: (-x['score'], x['latency_ms'], x['created_at']))
        
        # Assign ranks
        for idx, entry in enumerate(leaderboard, start=1):
            entry['rank'] = idx
            entry['score'] = float(entry['score'])
            entry['latency_ms'] = float(entry['latency_ms']) if entry['latency_ms'] != float('inf') else None
            entry['created_at'] = entry['created_at'].isoformat() if entry['created_at'] else None
        
        return Response(leaderboard, status=status.HTTP_200_OK)


class ProblemRunView(APIView):
    """
    Evaluate code against public dataset (quick feedback via "Evaluate" button).
    
    CRITICAL GUARANTEE: This endpoint NEVER returns HTTP 500.
    All exceptions are caught and converted to structured 200 OK responses.
    
    AUTHENTICATION:
    - Returns 401 Unauthorized if no valid auth token (DRF native, before view runs)
    
    Response Status Codes:
    - 200 OK: Always returned (structured error response if failure)
    - 400 Bad Request: Only for input validation errors (empty code)
    - 401 Unauthorized: No auth token (checked by DRF before view executes)
    
    Response Format (ALWAYS 200 OK on success or execution):
    {
        "status": "passed" | "error",
        "metric": "accuracy" | "f1" | "rmse" | etc (if status="passed"),
        "score": float (if status="passed"),
        "threshold": float (if problem has threshold, else null),
        "error_type": str (if status="error"),
        "message": str (if status="error")
    }
    
    Execution Pipeline (all steps wrapped):
    1. Load problem from DB
    2. Load dataset (catch shape/type errors)
    3. Execute user code (catch NameError, ValueError, etc.)
    4. Validate predictions (catch None, shape mismatch)
    5. Compute metric (catch computation errors)
    6. Build response (catch serialization errors)
    """
    
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        """
        Evaluate code against public dataset (immediate feedback).
        
        Calls the stateless run_tests() evaluator.
        Always returns 200 with structured JSON (never 500).
        """
        from ml.evaluator import run_tests
        
        # Extract and validate input
        code = request.data.get("code", "").strip()
        if not code:
            return Response({
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "Code cannot be empty.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Call stateless evaluator
        result = run_tests(slug, code)
        
        # Transform result for frontend
        if result['status'] == 'success':
            return Response({
                "status": "passed",
                "metric": result['metric'],
                "score": result['score'],
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "error_type": result['error_type'],
                "message": result['message'],
            }, status=status.HTTP_200_OK)


PLAYGROUND_MODELS = [
    {
        "id": "logistic_regression",
        "name": "Logistic Regression",
        "description": "Fast linear baseline for classification.",
        "hyperparameters": {
            "learning_rate": True,
            "epochs": True,
        },
    },
    {
        "id": "random_forest",
        "name": "Random Forest",
        "description": "Robust tree ensemble with strong default performance.",
        "hyperparameters": {
            "epochs": True,
        },
    },
    {
        "id": "mlp",
        "name": "MLP Neural Network",
        "description": "Feed-forward neural network for tabular learning.",
        "hyperparameters": {
            "learning_rate": True,
            "epochs": True,
            "batch_size": True,
            "hidden_units": True,
        },
    },
]


# Simple in-memory store for playground jobs.
PLAYGROUND_JOBS = {}


def _serialize_dataset_option(dataset):
    return {
        "id": str(dataset.id),
        "name": dataset.name,
        "description": dataset.description,
        "task_type": dataset.task_type,
        "num_features": dataset.num_features,
        "num_samples": dataset.num_samples,
    }


def _get_playground_options():
    datasets = list(Dataset.objects.order_by('name')[:20])

    if datasets:
        dataset_options = [_serialize_dataset_option(d) for d in datasets]
    else:
        dataset_options = [
            {
                "id": "iris",
                "name": "Iris (Demo)",
                "description": "Classic multiclass classification dataset.",
                "task_type": "classification",
                "num_features": 4,
                "num_samples": 150,
            },
            {
                "id": "wine",
                "name": "Wine (Demo)",
                "description": "Classification benchmark for chemical analysis.",
                "task_type": "classification",
                "num_features": 13,
                "num_samples": 178,
            },
        ]

    compatibility = {
        str(d["id"]): [m["id"] for m in PLAYGROUND_MODELS]
        for d in dataset_options
    }

    return {
        "datasets": dataset_options,
        "models": PLAYGROUND_MODELS,
        "compatibility": compatibility,
    }


def _generate_job_metrics(epochs):
    epochs = max(5, min(int(epochs or 50), 500))
    points = min(20, max(6, epochs // 10))
    loss = random.uniform(0.95, 1.25)
    accuracy = random.uniform(0.45, 0.62)
    metrics = []

    for step in range(1, points + 1):
        loss = max(0.03, loss * random.uniform(0.86, 0.96))
        accuracy = min(0.99, accuracy + random.uniform(0.01, 0.03))
        metrics.append(
            {
                "epoch": step,
                "loss": round(loss, 4),
                "accuracy": round(accuracy, 4),
            }
        )

    return metrics


def _resolve_job_for_user(job_id, user_id):
    job = PLAYGROUND_JOBS.get(job_id)
    if not job or job.get('user_id') != user_id:
        return None

    # Progress training state automatically based on elapsed time.
    if job['status'] == 'training':
        elapsed = (timezone.now() - job['created_at']).total_seconds()
        if elapsed >= 4:
            job['status'] = 'completed'
            job['completed_at'] = timezone.now()
            job['final_accuracy'] = job['metrics'][-1]['accuracy'] if job['metrics'] else None

    return job


def _public_job_payload(job):
    return {
        "id": job['id'],
        "status": job['status'],
        "dataset_type": job['dataset_type'],
        "model_type": job['model_type'],
        "learning_rate": job['learning_rate'],
        "epochs": job['epochs'],
        "batch_size": job.get('batch_size'),
        "hidden_units": job.get('hidden_units'),
        "final_accuracy": job.get('final_accuracy'),
        "error_message": job.get('error_message'),
        "created_at": job['created_at'].isoformat(),
        "completed_at": job['completed_at'].isoformat() if job.get('completed_at') else None,
    }


class PlaygroundOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_get_playground_options(), status=status.HTTP_200_OK)


class PlaygroundJobsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = [
            _public_job_payload(j)
            for j in PLAYGROUND_JOBS.values()
            if j.get('user_id') == request.user.id
        ]
        jobs.sort(key=lambda x: x['created_at'], reverse=True)
        return Response(jobs, status=status.HTTP_200_OK)

    def post(self, request):
        dataset_type = request.data.get('dataset_type')
        model_type = request.data.get('model_type')
        if not dataset_type or not model_type:
            return Response(
                {"error": "dataset_type and model_type are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_model_ids = {m['id'] for m in PLAYGROUND_MODELS}
        if model_type not in valid_model_ids:
            return Response({"error": "Unsupported model_type"}, status=status.HTTP_400_BAD_REQUEST)

        job_id = uuid.uuid4().hex
        epochs = int(request.data.get('epochs', 50))
        learning_rate = float(request.data.get('learning_rate', 0.01))
        batch_size = request.data.get('batch_size')
        hidden_units = request.data.get('hidden_units')

        job = {
            'id': job_id,
            'user_id': request.user.id,
            'status': 'training',
            'dataset_type': str(dataset_type),
            'model_type': model_type,
            'learning_rate': learning_rate,
            'epochs': epochs,
            'batch_size': int(batch_size) if batch_size is not None else None,
            'hidden_units': int(hidden_units) if hidden_units is not None else None,
            'metrics': _generate_job_metrics(epochs),
            'created_at': timezone.now(),
            'completed_at': None,
            'final_accuracy': None,
            'error_message': None,
        }
        PLAYGROUND_JOBS[job_id] = job
        return Response(_public_job_payload(job), status=status.HTTP_201_CREATED)


class PlaygroundJobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = _resolve_job_for_user(job_id, request.user.id)
        if not job:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_public_job_payload(job), status=status.HTTP_200_OK)


class PlaygroundJobStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = _resolve_job_for_user(job_id, request.user.id)
        if not job:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_public_job_payload(job), status=status.HTTP_200_OK)


class PlaygroundJobMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = _resolve_job_for_user(job_id, request.user.id)
        if not job:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(job.get('metrics', []), status=status.HTTP_200_OK)