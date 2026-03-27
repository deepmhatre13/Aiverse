"""Celery tasks for ML platform"""

from celery import shared_task
from django.core.cache import cache
import logging
import pickle
import tempfile
import subprocess
import json
import os

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def evaluate_submission(self, submission_id):
    """
    Evaluate ML submission using runner.py
    """
    try:
        from ml.models import Submission
        from ml.registry import get_problem_data
        
        submission = Submission.objects.get(id=submission_id)
        problem_def = get_problem_data(submission.problem.slug)
        
        if not problem_def:
            raise ValueError(f"Problem not found: {submission.problem.slug}")
        
        # Write data to temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            train_X_file = os.path.join(tmpdir, 'train_X.pkl')
            train_y_file = os.path.join(tmpdir, 'train_y.pkl')
            test_X_file = os.path.join(tmpdir, 'test_X.pkl')
            test_y_file = os.path.join(tmpdir, 'test_y.pkl')
            code_file = os.path.join(tmpdir, 'user_code.py')
            
            # Pickle datasets
            with open(train_X_file, 'wb') as f:
                pickle.dump(problem_def['X_train'], f)
            with open(train_y_file, 'wb') as f:
                pickle.dump(problem_def['y_train'], f)
            with open(test_X_file, 'wb') as f:
                pickle.dump(problem_def['X_test'], f)
            with open(test_y_file, 'wb') as f:
                pickle.dump(problem_def['y_test'], f)
            
            # Write user code
            with open(code_file, 'w') as f:
                f.write(submission.code)
            
            # Run sandbox
            runner_path = os.path.join(
                os.path.dirname(__file__),
                '../../sandbox/runner.py'
            )
            
            result = subprocess.run([
                'python',
                runner_path,
                '--train-X', train_X_file,
                '--train-y', train_y_file,
                '--test-X', test_X_file,
                '--test-y', test_y_file,
                '--metric', submission.problem.metric,
                '--user-code', code_file,
            ], capture_output=True, text=True, timeout=30)
            
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {
                    'status': 'error',
                    'error': f'Invalid output: {result.stdout}'
                }
            
            # Update submission
            if output.get('status') == 'success':
                submission.status = 'accepted'
                submission.score = output.get('score', 0)
            else:
                submission.status = 'rejected'
                submission.error = output.get('error', 'Unknown error')
            
            submission.save()
            logger.info(f"Submission {submission_id}: {submission.status}")
    
    except Exception as e:
        logger.error(f"Submission {submission_id} error: {e}")
        try:
            submission.status = 'error'
            submission.error = str(e)
            submission.save()
        except:
            pass


@shared_task(bind=True)
def train_playground_model(self, session_id):
    """
    Train model in playground session
    """
    try:
        from ml_playground.models import PlaygroundSession
        from ml.registry import get_problem_data
        
        session = PlaygroundSession.objects.get(id=session_id)
        problem_def = get_problem_data(session.problem.slug)
        
        if not problem_def:
            raise ValueError(f"Problem not found: {session.problem.slug}")
        
        # Similar to evaluate_submission
        with tempfile.TemporaryDirectory() as tmpdir:
            train_X_file = os.path.join(tmpdir, 'train_X.pkl')
            train_y_file = os.path.join(tmpdir, 'train_y.pkl')
            test_X_file = os.path.join(tmpdir, 'test_X.pkl')
            test_y_file = os.path.join(tmpdir, 'test_y.pkl')
            code_file = os.path.join(tmpdir, 'user_code.py')
            
            with open(train_X_file, 'wb') as f:
                pickle.dump(problem_def['X_train'], f)
            with open(train_y_file, 'wb') as f:
                pickle.dump(problem_def['y_train'], f)
            with open(test_X_file, 'wb') as f:
                pickle.dump(problem_def['X_test'], f)
            with open(test_y_file, 'wb') as f:
                pickle.dump(problem_def['y_test'], f)
            
            with open(code_file, 'w') as f:
                f.write(session.code)
            
            runner_path = os.path.join(
                os.path.dirname(__file__),
                '../../sandbox/runner.py'
            )
            
            result = subprocess.run([
                'python',
                runner_path,
                '--train-X', train_X_file,
                '--train-y', train_y_file,
                '--test-X', test_X_file,
                '--test-y', test_y_file,
                '--metric', session.problem.metric,
                '--user-code', code_file,
            ], capture_output=True, text=True, timeout=30)
            
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = {
                    'status': 'error',
                    'error': f'Invalid output: {result.stdout}'
                }
            
            session.status = 'completed'
            if output.get('status') == 'success':
                session.score = output.get('score', 0)
                session.result = output
            else:
                session.error = output.get('error', 'Unknown error')
            
            session.save()
            logger.info(f"Playground {session_id}: completed")
    
    except Exception as e:
        logger.error(f"Playground {session_id} error: {e}")
        try:
            session.status = 'failed'
            session.error = str(e)
            session.save()
        except:
            pass
