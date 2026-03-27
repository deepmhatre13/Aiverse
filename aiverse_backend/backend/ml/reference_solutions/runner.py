"""
Reference Solution Runner — Admin-Only Utility

This module runs reference solutions for problems to:
1. Calibrate submission thresholds
2. Verify metric correctness
3. Validate problem datasets

SECURITY:
- This module should ONLY be called from admin views/management commands
- Output should NEVER be serialized to API responses
- Solutions should NEVER be logged or exposed

Usage (admin command):
    python manage.py test_reference_solution linear-binary-classification
    
Usage (admin view):
    from ml.reference_solutions import run_reference_solution
    result = run_reference_solution('linear-binary-classification')
"""

import os
import importlib.util
import logging
from typing import Dict, Optional, Any
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Path to solutions directory
SOLUTIONS_DIR = Path(__file__).parent / 'solutions'


def list_available_solutions() -> list:
    """List all available reference solution slugs."""
    if not SOLUTIONS_DIR.exists():
        return []
    
    solutions = []
    for f in SOLUTIONS_DIR.glob('*.py'):
        if f.name.startswith('_'):
            continue
        slug = f.stem.replace('_', '-')
        solutions.append(slug)
    return sorted(solutions)


def _load_solution_module(problem_slug: str):
    """
    Load a reference solution module for a given problem.
    
    Args:
        problem_slug: Problem slug (e.g., 'linear-binary-classification')
        
    Returns:
        Module object with train_and_predict function
        
    Raises:
        FileNotFoundError: If solution file doesn't exist
        ImportError: If solution module can't be loaded
    """
    # Convert slug to filename (linear-binary-classification -> linear_binary_classification.py)
    filename = problem_slug.replace('-', '_') + '.py'
    filepath = SOLUTIONS_DIR / filename
    
    if not filepath.exists():
        raise FileNotFoundError(
            f"Reference solution not found: {filepath}\n"
            f"Available solutions: {list_available_solutions()}"
        )
    
    # Load module dynamically
    spec = importlib.util.spec_from_file_location(
        f"reference_solution_{problem_slug}", filepath
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Verify train_and_predict exists
    if not hasattr(module, 'train_and_predict'):
        raise ImportError(
            f"Reference solution {filepath} must define train_and_predict function"
        )
    
    return module


def run_reference_solution(
    problem_slug: str,
    metric: Optional[str] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a reference solution for a problem and return the score.
    
    This function:
    1. Loads the problem definition from registry
    2. Loads the reference solution
    3. Runs the solution on the visible dataset
    4. Computes the metric
    5. Returns structured result (NEVER exposed to users)
    
    Args:
        problem_slug: Problem slug identifier
        metric: Optional metric override (uses problem default if None)
        verbose: Print debug information
        
    Returns:
        {
            'status': 'success' | 'error',
            'score': float,
            'threshold': float,
            'meets_threshold': bool,
            'metric': str,
            'latency_ms': float,
            'error': str (if status == 'error')
        }
        
    SECURITY: This result should NEVER be exposed to users.
    """
    import time
    from ml.registry import get_problem_definition
    from ml.metrics import compute_metric, LOWER_IS_BETTER_METRICS
    
    try:
        # Load problem definition
        problem_def = get_problem_definition(problem_slug)
        
        # Determine metric
        eval_metric = metric or problem_def.default_metric
        
        # Load reference solution
        solution_module = _load_solution_module(problem_slug)
        train_and_predict = solution_module.train_and_predict
        
        # Load and split dataset
        X, y, metadata = problem_def.load_full_dataset()
        
        if problem_def.task_type == 'classification':
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
        
        # Execute reference solution
        start_time = time.perf_counter()
        predictions = train_and_predict(X_train, y_train, X_test)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        # Validate predictions
        predictions = np.array(predictions)
        if len(predictions) != len(y_test):
            raise ValueError(
                f"Prediction length mismatch: expected {len(y_test)}, got {len(predictions)}"
            )
        
        # Compute metric
        score = compute_metric(y_test, predictions, eval_metric)
        
        # Determine if threshold is met
        threshold = problem_def.submission_threshold
        lower_is_better = eval_metric.lower() in LOWER_IS_BETTER_METRICS
        
        if lower_is_better:
            meets_threshold = score <= threshold
        else:
            meets_threshold = score >= threshold
        
        if verbose:
            logger.info(
                f"Reference solution for {problem_slug}: "
                f"score={score:.4f}, threshold={threshold}, meets={meets_threshold}"
            )
        
        return {
            'status': 'success',
            'score': float(score),
            'threshold': float(threshold),
            'meets_threshold': meets_threshold,
            'metric': eval_metric,
            'latency_ms': float(latency_ms),
            'higher_is_better': not lower_is_better,
        }
        
    except Exception as e:
        logger.error(f"Reference solution error for {problem_slug}: {e}")
        return {
            'status': 'error',
            'error': str(e),
        }


def get_reference_score(problem_slug: str, metric: Optional[str] = None) -> Optional[float]:
    """
    Get just the reference score for a problem.
    
    Returns None on error.
    """
    result = run_reference_solution(problem_slug, metric)
    if result['status'] == 'success':
        return result['score']
    return None


def validate_threshold(problem_slug: str, proposed_threshold: float) -> Dict[str, Any]:
    """
    Validate that a proposed threshold is achievable by the reference solution.
    
    Args:
        problem_slug: Problem slug
        proposed_threshold: Threshold to validate
        
    Returns:
        {
            'valid': bool,
            'reference_score': float,
            'proposed_threshold': float,
            'buffer_percent': float,  # How much margin above/below threshold
            'recommendation': str
        }
    """
    from ml.registry import get_problem_definition
    from ml.metrics import LOWER_IS_BETTER_METRICS
    
    result = run_reference_solution(problem_slug)
    
    if result['status'] == 'error':
        return {
            'valid': False,
            'error': result['error'],
        }
    
    problem_def = get_problem_definition(problem_slug)
    lower_is_better = result['metric'].lower() in LOWER_IS_BETTER_METRICS
    
    score = result['score']
    
    if lower_is_better:
        valid = score <= proposed_threshold
        buffer = ((proposed_threshold - score) / proposed_threshold) * 100
    else:
        valid = score >= proposed_threshold
        buffer = ((score - proposed_threshold) / proposed_threshold) * 100
    
    recommendation = ""
    if not valid:
        recommendation = f"Reference solution score ({score:.4f}) does not meet proposed threshold ({proposed_threshold})."
    elif buffer < 5:
        recommendation = f"Warning: Only {buffer:.1f}% buffer between reference score and threshold. Consider adjusting."
    elif buffer > 50:
        recommendation = f"Threshold may be too easy. Reference achieves {buffer:.1f}% better than threshold."
    else:
        recommendation = f"Threshold looks reasonable with {buffer:.1f}% buffer."
    
    return {
        'valid': valid,
        'reference_score': score,
        'proposed_threshold': proposed_threshold,
        'buffer_percent': buffer,
        'recommendation': recommendation,
        'metric': result['metric'],
        'higher_is_better': not lower_is_better,
    }
