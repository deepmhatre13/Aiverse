import time
import traceback
from celery import shared_task


@shared_task
def evaluate_submission(submission_id):
    """
    Evaluate a user's ML code submission against private evaluation dataset.
    
    This is an ORCHESTRATOR task that:
    1. Fetches Submission from DB
    2. Calls the stateless evaluate_code() evaluator
    3. Persists results to DB
    
    Submission Lifecycle (STRICT STATE MACHINE):
    pending (initial) → running → (passed | failed | error) [terminal]
    
    CRITICAL:
    - Import models INSIDE task (prevents AppRegistryNotReady)
    - Call run_tests() for actual evaluation (no duplication)
    - Update submission with results
    """
    
    # Import INSIDE task to avoid AppRegistryNotReady
    from ml.models import Submission
    from ml.evaluator import run_tests
    
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        return  # Silently exit if submission was deleted
    
    # ================================================================
    # STEP 1: Mark as Running (State Transition: pending → running)
    # ================================================================
    submission.status = 'running'
    submission.save(update_fields=['status'])
    
    try:
        problem_slug = submission.problem.slug
        user_code = submission.code
        
        start_time = time.time()
        
        # ================================================================
        # STEP 2: Call Stateless Evaluator
        # ================================================================
        # run_tests() returns:
        # {
        #   "status": "success" | "error",
        #   "metric": "accuracy" | "f1" | "rmse" | etc,
        #   "score": float,
        #   "error_type": "VALIDATION_ERROR" | "RUNTIME_ERROR" | "TIMEOUT_ERROR",
        #   "message": str,
        # }
        result = run_tests(problem_slug, user_code)
        
        runtime = time.time() - start_time
        
        # ================================================================
        # STEP 3: Persist Results (State Transition: running → passed/failed/error)
        # ================================================================
        if result['status'] == 'success':
            submission.status = 'passed'
            submission.public_score = result['score']
            submission.private_score = result['score']
            submission.error_log = ''
        else:
            submission.status = 'failed'
            submission.public_score = 0.0
            submission.private_score = 0.0
            submission.error_log = f"{result['error_type']}: {result['message']}"
        
        submission.runtime_seconds = runtime
        submission.save(update_fields=[
            'status',
            'public_score',
            'private_score',
            'error_log',
            'runtime_seconds'
        ])
    
    except Exception as e:
        # Unexpected error during orchestration
        # State Transition: running → error
        submission.status = 'error'
        submission.error_log = traceback.format_exc()
        submission.runtime_seconds = time.time() - start_time
        submission.save(update_fields=[
            'status',
            'error_log',
            'runtime_seconds'
        ])

