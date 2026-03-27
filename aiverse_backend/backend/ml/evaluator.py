import traceback
import time
import sys
import numpy as np

from ml.registry import get_problem_definition
from ml.sandbox import execute_user_code
from ml.metrics import compute_metric, LOWER_IS_BETTER_METRICS
from ml.validators import (
    validate_code_not_empty,
    validate_imports,
    validate_function_exists,
    validate_function_signature,
    validate_predictions,
)


def _estimate_memory_bytes(predictions):
    """Estimate memory usage of predictions array in bytes."""
    if isinstance(predictions, np.ndarray):
        return predictions.nbytes
    if isinstance(predictions, (list, tuple)):
        return sys.getsizeof(predictions)
    return sys.getsizeof(predictions)


def _is_lower_better(metric_name: str) -> bool:
    """Check if a metric is lower-is-better."""
    return metric_name.lower().strip() in LOWER_IS_BETTER_METRICS


def _meets_threshold(score: float, threshold: float, metric_name: str) -> bool:
    """
    Determine whether a score meets the threshold.

    For lower-is-better metrics (rmse, mae, mse), meeting the threshold
    means the score is less than or equal to the threshold.
    For higher-is-better metrics, the score must be greater than or equal.
    """
    if _is_lower_better(metric_name):
        return score <= threshold
    return score >= threshold


def _check_constraints(constraints: dict, latency_ms: float, memory_bytes: int) -> dict:
    """
    Check problem constraints against measured values.

    Returns a dict with:
        - constraints_met: bool
        - reason: str or None (only set when a constraint is violated)
    """
    if not constraints:
        return {"constraints_met": True, "reason": None}

    max_latency = constraints.get("max_latency_ms")
    if max_latency is not None and latency_ms > max_latency:
        return {
            "constraints_met": False,
            "reason": f"Latency {latency_ms:.1f}ms exceeds max_latency_ms constraint ({max_latency}ms)",
        }

    max_memory = constraints.get("max_memory_bytes")
    if max_memory is not None and memory_bytes > max_memory:
        return {
            "constraints_met": False,
            "reason": f"Memory usage {memory_bytes} bytes exceeds max_memory_bytes constraint ({max_memory} bytes)",
        }

    return {"constraints_met": True, "reason": None}


def run_tests(problem_slug: str, user_code: str):
    """
    Enhanced stateless evaluator for "Evaluate".

    - Validates user code
    - Executes code against visible dataset with latency measurement
    - Validates prediction shape
    - Estimates memory usage
    - Computes metric with direction-aware threshold checking
    - Evaluates against hidden dataset when hidden_test_ratio > 0
    - Enforces constraints from ProblemDefinition
    - Returns structured JSON with comprehensive evaluation info
    - NEVER touches Submission or DB

    Args:
        problem_slug: Problem identifier (e.g., "iris-species-classification")
        user_code: User-submitted Python code string

    Returns:
        {
            "status": "success" | "error",
            "metric": str,
            "score": float,
            "threshold": float | None,
            "meets_threshold": bool,
            "latency_ms": float,
            "prediction_shape": list,
            "memory_estimate_bytes": int,
            "hidden_score": float (if hidden tests exist),
            "constraints_met": bool (if constraints exist),
            "reason": str (if meets_threshold is False due to constraint violation),
            --- or on error ---
            "error_type": str,
            "message": str,
        }
    """

    try:
        # 1. Basic validation
        validate_code_not_empty(user_code)
        validate_imports(user_code)
        validate_function_exists(user_code, "train_and_predict")
        validate_function_signature(user_code, expected_args=3)

        # 2. Load problem definition
        problem = get_problem_definition(problem_slug)

        X_train, y_train, X_test, y_test = problem.load_visible_dataset()

        # 3. Execute user code with performance tracking
        predictions, latency_ms, memory_mb = execute_user_code(
            user_code=user_code,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
        )
        latency_ms = round(latency_ms, 2)

        # 4. Validate predictions
        validate_predictions(predictions, expected_len=len(y_test))

        # 5. Prediction shape validation
        predictions_array = np.asarray(predictions)
        prediction_shape = list(predictions_array.shape)

        # 6. Memory conversion (MB to bytes for backward compatibility)
        memory_bytes = int(memory_mb * 1024 * 1024) if memory_mb else _estimate_memory_bytes(predictions_array)

        # 7. Compute metric on visible dataset
        metric_name = problem.default_metric
        score = compute_metric(
            metric=metric_name,
            y_true=y_test,
            y_pred=predictions,
        )

        # 8. Build base response
        response = {
            "status": "success",
            "metric": metric_name,
            "score": round(float(score), 4),
            "threshold": problem.submission_threshold,
            "latency_ms": latency_ms,
            "memory_mb": round(memory_mb, 2),
            "prediction_shape": prediction_shape,
            "memory_estimate_bytes": memory_bytes,
        }

        # 9. Determine meets_threshold with metric-direction awareness
        if problem.submission_threshold is not None:
            meets = _meets_threshold(score, problem.submission_threshold, metric_name)
            response["meets_threshold"] = meets
        else:
            response["meets_threshold"] = None

        # 10. Hidden test evaluation
        if getattr(problem, "hidden_test_ratio", 0) and problem.hidden_test_ratio > 0:
            try:
                (
                    h_X_train,
                    h_y_train,
                    _h_X_vis_test,
                    _h_y_vis_test,
                    X_hidden,
                    y_hidden,
                ) = problem.load_hidden_dataset()

                hidden_predictions = execute_user_code(
                    user_code=user_code,
                    X_train=h_X_train,
                    y_train=h_y_train,
                    X_test=X_hidden,
                )

                validate_predictions(hidden_predictions, expected_len=len(y_hidden))

                hidden_score = compute_metric(
                    metric=metric_name,
                    y_true=y_hidden,
                    y_pred=hidden_predictions,
                )
                response["hidden_score"] = round(float(hidden_score), 4)
            except Exception:
                # Hidden test failure should not block visible test results
                response["hidden_score"] = None
                response["hidden_test_error"] = "Hidden test evaluation failed"

        # 11. Constraint enforcement
        constraints = getattr(problem, "constraints", None)
        if constraints:
            constraint_result = _check_constraints(constraints, latency_ms, memory_bytes)
            response["constraints_met"] = constraint_result["constraints_met"]

            if not constraint_result["constraints_met"]:
                response["meets_threshold"] = False
                response["reason"] = constraint_result["reason"]
        else:
            response["constraints_met"] = None

        return response

    except ValueError as e:
        return {
            "status": "error",
            "error_type": "VALIDATION_ERROR",
            "message": str(e),
        }
    except Exception as e:
        # Catches TimeoutException and any runtime errors
        if "timeout" in str(e).lower():
            return {
                "status": "error",
                "error_type": "TIMEOUT_ERROR",
                "message": "Code execution exceeded 5-second timeout.",
            }
        return {
            "status": "error",
            "error_type": "RUNTIME_ERROR",
            "message": str(e),
        }
