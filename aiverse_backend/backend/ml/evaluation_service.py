"""
Core ML evaluation service.
Handles code validation, execution, and metric computation.
"""

from typing import Dict, Tuple, Optional
import traceback
from ml.validators import (
    validate_code_not_empty,
    validate_imports,
    validate_function_exists,
    validate_function_signature,
    validate_predictions,
    validate_task_type,
)
from ml.metrics import compute_metric, HIGHER_IS_BETTER_METRICS, LOWER_IS_BETTER_METRICS
from ml.sandbox import execute_user_code, TimeoutException
from ml.registry import get_problem_definition


class EvaluationError(Exception):
    """Base class for evaluation errors."""
    
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type
        self.message = message
        super().__init__(message)


def evaluate_code(
    problem_slug: str,
    user_code: str,
    metric: Optional[str] = None
) -> Dict:
    """
    Evaluate user code against a problem.
    
    Args:
        problem_slug: Problem identifier
        user_code: Python code with train_and_predict function
        metric: Metric to compute (uses default if None)
    
    Returns:
        {
            "status": "success" | "error",
            "metric": str,
            "score": float,
            "threshold": float or None,
            "meets_threshold": bool,
            "error_type": str (if error),
            "message": str (if error)
        }
    
    Success response ALWAYS includes:
        - status
        - metric
        - score
        - threshold (can be null)
        - meets_threshold
    
    Error response ALWAYS includes:
        - status
        - error_type
        - message
    """
    
    try:
        # STEP 1: Validate code format
        try:
            validate_code_not_empty(user_code)
            validate_imports(user_code)  # CHANGED: Validate imports are restricted
            validate_function_exists(user_code, "train_and_predict")
            validate_function_signature(user_code, "train_and_predict", expected_args=3)
        except ValueError as e:
            return {
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": str(e)
            }
        
        # STEP 2: Get problem definition
        try:
            problem_def = get_problem_definition(problem_slug)
        except ValueError as e:
            return {
                "status": "error",
                "error_type": "CONFIG_ERROR",
                "message": f"Problem not found: {problem_slug}"
            }
        
        # STEP 3: Determine metric
        eval_metric = metric or problem_def.default_metric
        if eval_metric not in problem_def.allowed_metrics:
            return {
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": f"Invalid metric '{eval_metric}'. Allowed metrics: {', '.join(problem_def.allowed_metrics)}"
            }
        
        # STEP 4: Load full dataset and split deterministically
        try:
            from sklearn.model_selection import train_test_split
            X, y, metadata = problem_def.load_full_dataset()

            # Perform deterministic split based on task type
            if metadata['task_type'] == 'classification':
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
            else:  # regression
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42
                )
        except Exception as e:
            return {
                "status": "error",
                "error_type": "DATA_ERROR",
                "message": f"Failed to load dataset: {str(e)}"
            }

        # STEP 5: Validate split sizes
        try:
            expected_test_size = int(0.2 * len(X))
            if len(X_test) != expected_test_size:
                return {
                    "status": "error",
                    "error_type": "DATA_ERROR",
                    "message": f"Invalid test split size: expected {expected_test_size}, got {len(X_test)}"
                }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "DATA_ERROR",
                "message": f"Failed to validate split: {str(e)}"
            }
        
        # STEP 6: Execute user code and measure performance
        try:
            predictions, latency_ms, memory_mb = execute_user_code(user_code, X_train, y_train, X_test)
        except TimeoutException:
            return {
                "status": "error",
                "error_type": "TIMEOUT_ERROR",
                "message": "Code execution exceeded 5-second timeout. Try optimizing your code for faster execution."
            }
        except Exception as e:
            # Provide user-friendly error messages
            error_msg = str(e)
            if "train_and_predict" in error_msg.lower():
                if "not defined" in error_msg.lower() or "not found" in error_msg.lower():
                    return {
                        "status": "error",
                        "error_type": "VALIDATION_ERROR",
                        "message": "You must define a function named `train_and_predict(X_train, y_train, X_test)`. Make sure the function name matches exactly."
                    }
                elif "not callable" in error_msg.lower():
                    return {
                        "status": "error",
                        "error_type": "VALIDATION_ERROR",
                        "message": "`train_and_predict` must be a function. Check that you defined it with `def train_and_predict(...)`."
                    }
            elif "predictions" in error_msg.lower() and ("not defined" in error_msg.lower() or "not assigned" in error_msg.lower()):
                return {
                    "status": "error",
                    "error_type": "RUNTIME_ERROR",
                    "message": "You returned `predictions` but never assigned it. Did you forget to call `model.predict(X_test)`?"
                }
            elif "NameError" in str(type(e).__name__):
                return {
                    "status": "error",
                    "error_type": "RUNTIME_ERROR",
                    "message": f"Variable or function not found: {error_msg}. Check your imports and variable names."
                }
            elif "ValueError" in str(type(e).__name__):
                return {
                    "status": "error",
                    "error_type": "RUNTIME_ERROR",
                    "message": f"Invalid value: {error_msg}. Check your data shapes and model parameters."
                }
            else:
                return {
                    "status": "error",
                    "error_type": "RUNTIME_ERROR",
                    "message": f"Code execution failed: {error_msg}"
                }

        # STEP 7: Validate predictions
        try:
            validate_predictions(predictions, expected_len=len(y_test))
        except ValueError as e:
            return {
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": f"Invalid predictions: {str(e)}"
            }

        # STEP 8: Validate task type (classification vs regression)
        try:
            validate_task_type(problem_def.task_type, y_test, predictions)
        except ValueError as e:
            return {
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": str(e)
            }

        # STEP 9: Compute metric
        try:
            score = compute_metric(eval_metric, y_test, predictions)
            score = round(float(score), 4)
        except Exception as e:
            return {
                "status": "error",
                "error_type": "METRIC_ERROR",
                "message": f"Metric computation failed: {str(e)}"
            }

        # STEP 10: Check threshold
        threshold = problem_def.submission_threshold
        higher_is_better = problem_def.higher_is_better  # From registry

        if threshold is None:
            meets_threshold = True
        elif higher_is_better:
            meets_threshold = score >= threshold
        else:
            # Lower is better (rmse, mae, mse)
            meets_threshold = score <= threshold
        
        # STEP 11: Check resource constraints (if problem has limits)
        # Note: These checks are informational - they don't fail the submission
        # but are stored for leaderboard sorting
        
        return {
            "status": "success",
            "metric": eval_metric,
            "score": score,
            "threshold": threshold,
            "higher_is_better": higher_is_better,
            "meets_threshold": meets_threshold,
            "latency_ms": round(latency_ms, 2),
            "memory_mb": round(memory_mb, 2),
            "verdict": "ACCEPTED" if meets_threshold else "REJECTED",
        }
    
    except Exception as e:
        # Internal evaluation error - should rarely occur if all validation passes
        import traceback
        return {
            "status": "error",
            "error_type": "INTERNAL_ERROR",
            "message": "Evaluation failed due to an internal error",
            "stack_trace": traceback.format_exc() if __debug__ else None
        }
