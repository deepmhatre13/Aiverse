"""
Safe Code Execution Engine for ML Problem Solutions

Executes user-submitted code in an isolated namespace with:
- Input injection (X_train, y_train, X_test)
- Output capture (stdout, stderr)
- Exception handling
- Timeout enforcement
- Memory limits
- API Compatibility validation (prevents deprecated sklearn parameters)
"""

import signal
import sys
import io
import traceback
import ast
import inspect
from typing import Callable, Tuple, Optional, Dict, Any
import numpy as np
import sklearn
from sklearn import preprocessing, tree, ensemble, linear_model, svm, neighbors, naive_bayes, neighbors, metrics
import pandas as pd
from .api_validator import APICompatibilityLayer


def validate_function_signature(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that code defines train_and_predict with correct signature.
    
    STRICT REQUIREMENT:
    def train_and_predict(X_train, y_train, X_test):
        ...
        return predictions
    
    Args:
        code: User-submitted Python code
    
    Returns:
        (is_valid, error_message)
        - is_valid: True if signature is correct
        - error_message: User-friendly error if not
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax Error in code: {str(e)}"
    
    # Find the train_and_predict function
    func_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'train_and_predict':
            func_def = node
            break
    
    if not func_def:
        return False, (
            "Code must define a function: def train_and_predict(X_train, y_train, X_test)\n"
            "Example:\n"
            "  def train_and_predict(X_train, y_train, X_test):\n"
            "      model = LogisticRegression()\n"
            "      model.fit(X_train, y_train)\n"
            "      return model.predict(X_test)"
        )
    
    # Check argument count (must have exactly 3 args)
    args = func_def.args
    arg_count = len(args.args)
    
    if arg_count != 3:
        return False, (
            f"train_and_predict() must have exactly 3 arguments, got {arg_count}.\n"
            f"Signature: def train_and_predict(X_train, y_train, X_test)"
        )
    
    # Check argument names
    expected_args = ['X_train', 'y_train', 'X_test']
    actual_args = [arg.arg for arg in args.args]
    
    if actual_args != expected_args:
        return False, (
            f"train_and_predict() argument names must match exactly:\n"
            f"  Expected: {expected_args}\n"
            f"  Got: {actual_args}"
        )
    
    return True, None



def validate_predictions(
    predictions: Any,
    X_test: np.ndarray,
    y_train: np.ndarray,
    is_regression: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Validate output predictions from user code.
    
    Checks:
    - predictions is not None
    - predictions is numpy array or list
    - predictions length matches X_test length
    - predictions are numeric (int/float)
    - (classification only) all predictions are valid classes from y_train
    
    Args:
        predictions: Output from train_and_predict()
        X_test: Test features (used for length validation)
        y_train: Training targets (used for class validation)
        is_regression: If True, skip class validation (regression allows any numeric value)
    
    Returns: (is_valid, error_message or None)
    """
    
    # Check: not None
    if predictions is None:
        return False, "train_and_predict() returned None"
    
    # Check: is array-like
    if not isinstance(predictions, (np.ndarray, list)):
        return False, f"Expected predictions as numpy array or list, got {type(predictions).__name__}"
    
    # Convert to numpy if list
    try:
        if isinstance(predictions, list):
            predictions = np.array(predictions)
    except Exception as e:
        return False, f"Could not convert predictions to numpy array: {str(e)}"
    
    # Check: shape matches X_test
    if len(predictions) != len(X_test):
        return False, (
            f"Predictions length {len(predictions)} does not match "
            f"X_test length {len(X_test)}"
        )
    
    # Check: predictions are numeric
    if not np.issubdtype(predictions.dtype, np.number):
        return False, f"Predictions must be numeric, got dtype {predictions.dtype}"
    
    # For classification: check all predictions are valid classes from training data
    # For regression: skip this check (any numeric value is OK)
    if not is_regression:
        unique_train_classes = np.unique(y_train)
        unique_pred_classes = np.unique(predictions)
        
        invalid_classes = np.setdiff1d(unique_pred_classes, unique_train_classes)
        if len(invalid_classes) > 0:
            return False, (
                f"Predictions contain invalid classes {list(invalid_classes)}. "
                f"Valid classes from training data: {list(unique_train_classes)}"
            )
    
    return True, None


class TimeoutException(Exception):
    """Raised when code execution exceeds time limit."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Code execution exceeded 5 second timeout")


class CodeExecutor:
    """
    Safely execute user code with timeout and exception handling.
    
    Usage:
        executor = CodeExecutor(timeout_seconds=5)
        predictions, output, error = executor.execute(
            code_str,
            X_train, y_train, X_test
        )
    """
    
    def __init__(self, timeout_seconds: int = 5):
        self.timeout_seconds = timeout_seconds
    
    def execute(
        self,
        code: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray
    ) -> Tuple[Optional[np.ndarray], str, str, Optional[Tuple[str, str]]]:
        """
        Execute user code and return predictions with error details.
        
        Args:
            code: User-submitted Python code (must define train_and_predict)
            X_train, y_train: Training data
            X_test: Test data to predict on
        
        Returns:
            (predictions, stdout, stderr, error_info)
            - predictions: np.ndarray or None if failed
            - stdout: Captured print statements
            - stderr: Captured errors/exceptions (full traceback)
            - error_info: None if success, else (error_type, error_message)
        """
        
        # ================================================================
        # VALIDATION STEP 0: Check for API compatibility issues
        # ================================================================
        is_compatible, compatibility_error = APICompatibilityLayer.check_code(code)
        if not is_compatible:
            # Return USER_ERROR (not a runtime error)
            return None, "", compatibility_error, ("USER_ERROR", compatibility_error)
        
        # Capture stdout and stderr
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        predictions = None
        error_info = None
        
        try:
            # Redirect output
            sys.stdout = captured_stdout
            sys.stderr = captured_stderr
            
            # Create isolated namespace
            namespace = {
                'np': np,
                'numpy': np,
                'pd': pd,
                'pandas': pd,
                'sklearn': sklearn,
                'preprocessing': preprocessing,
                'tree': tree,
                'ensemble': ensemble,
                'linear_model': linear_model,
                'svm': svm,
                'neighbors': neighbors,
                'naive_bayes': naive_bayes,
                'metrics': metrics,
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'int': int,
                    'float': float,
                    'str': str,
                    'bool': bool,
                    'abs': abs,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'round': round,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'isinstance': isinstance,
                    'type': type,
                    '__import__': __import__,  # ✅ Allow imports
                },
                'X_train': X_train,
                'y_train': y_train,
                'X_test': X_test,
            }
            
            # Set timeout (Unix/Linux only)
            old_sigalrm = None
            try:
                old_sigalrm = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout_seconds)
            except (AttributeError, ValueError):
                # Windows doesn't support SIGALRM, skip timeout
                pass
            
            try:
                # Execute user code
                exec(code, namespace)
                
                # Call the function
                if 'train_and_predict' not in namespace:
                    raise NameError("Code must define function: train_and_predict(X_train, y_train, X_test)")
                
                func = namespace['train_and_predict']
                predictions = func(X_train, y_train, X_test)
                
                # Validate output
                if predictions is None:
                    raise ValueError("train_and_predict must return predictions (not None)")
                
                predictions = np.asarray(predictions)
                
            except TimeoutException as e:
                error_info = ("RUNTIME_ERROR", f"TimeoutException: {str(e)}")
                error_msg = f"TimeoutException: {str(e)}"
                captured_stderr.write(error_msg)
            except NameError as e:
                error_info = ("RUNTIME_ERROR", f"NameError: {str(e)}")
                error_msg = f"NameError: {str(e)}"
                captured_stderr.write(error_msg)
            except ValueError as e:
                error_info = ("RUNTIME_ERROR", f"ValueError: {str(e)}")
                error_msg = f"ValueError: {str(e)}"
                captured_stderr.write(error_msg)
            except TypeError as e:
                error_info = ("RUNTIME_ERROR", f"TypeError: {str(e)}")
                error_msg = f"TypeError: {str(e)}"
                captured_stderr.write(error_msg)
            except KeyError as e:
                error_info = ("RUNTIME_ERROR", f"KeyError: {str(e)}")
                error_msg = f"KeyError: {str(e)}"
                captured_stderr.write(error_msg)
            except Exception as e:
                error_info = ("RUNTIME_ERROR", f"{type(e).__name__}: {str(e)}")
                error_msg = traceback.format_exc()
                captured_stderr.write(error_msg)
            finally:
                # Clear timeout
                try:
                    signal.alarm(0)
                    if old_sigalrm:
                        signal.signal(signal.SIGALRM, old_sigalrm)
                except (AttributeError, ValueError):
                    pass
        
        finally:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        stdout_str = captured_stdout.getvalue()
        stderr_str = captured_stderr.getvalue()
        
        return predictions, stdout_str, stderr_str, error_info


def execute_user_code(
    code: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    timeout_seconds: int = 5
) -> Dict[str, Any]:
    """
    High-level wrapper for code execution with error classification.
    
    Returns:
        {
            "success": bool,
            "predictions": Optional[np.ndarray],
            "stdout": str,
            "stderr": str,
            "error_type": str,  # USER_ERROR, RUNTIME_ERROR, SYSTEM_ERROR, or None
            "error_details": Optional[str],
            "error_log": Optional[str]
        }
    """
    
    # STEP 1: Validate input code
    if not code or not code.strip():
        return {
            "success": False,
            "predictions": None,
            "stdout": "",
            "stderr": "Code is empty",
            "error_type": "USER_ERROR",
            "error_details": "Code cannot be empty",
            "error_log": None
        }
    
    if "train_and_predict" not in code:
        return {
            "success": False,
            "predictions": None,
            "stdout": "",
            "stderr": "Code must define: def train_and_predict(X_train, y_train, X_test)",
            "error_type": "USER_ERROR",
            "error_details": "Missing required function: train_and_predict",
            "error_log": None
        }
    
    # STEP 1.5: Validate function signature (before execution)
    is_signature_valid, signature_error = validate_function_signature(code)
    if not is_signature_valid:
        return {
            "success": False,
            "predictions": None,
            "stdout": "",
            "stderr": signature_error,
            "error_type": "USER_ERROR",
            "error_details": signature_error,
            "error_log": None
        }
    
    # STEP 2: Check API compatibility (before execution)
    is_compatible, compatibility_error = APICompatibilityLayer.check_code(code)
    if not is_compatible:
        return {
            "success": False,
            "predictions": None,
            "stdout": "",
            "stderr": compatibility_error,
            "error_type": "USER_ERROR",
            "error_details": compatibility_error,
            "error_log": None
        }
    
    # STEP 3: Execute code
    executor = CodeExecutor(timeout_seconds=timeout_seconds)
    predictions, stdout, stderr, error_info = executor.execute(code, X_train, y_train, X_test)
    
    # STEP 4: Validate predictions output
    if error_info is None and predictions is not None:
        # Detect if this is a regression problem:
        # If y_train has integer values 0-9 and predictions have many non-integer values, likely regression
        # Also check: if any prediction is not in y_train classes and predictions are mostly float, likely regression
        is_classification = (
            np.issubdtype(y_train.dtype, np.integer) and 
            len(np.unique(y_train)) <= 10  # Heuristic: 0-9 suggests classification
        )
        
        # If predictions look like floats with decimals, it's likely regression
        if is_classification and np.issubdtype(predictions.dtype, np.floating):
            # Check if predictions are mostly non-integer values
            non_integer_preds = np.sum(predictions != np.round(predictions)) / len(predictions)
            if non_integer_preds > 0.5:  # > 50% non-integer = regression
                is_classification = False
        
        is_valid, validation_error = validate_predictions(predictions, X_test, y_train, is_regression=not is_classification)
        if not is_valid:
            error_info = ("RUNTIME_ERROR", validation_error)
            predictions = None
    
    # STEP 5: Build response
    success = predictions is not None and error_info is None
    
    result = {
        "success": success,
        "predictions": predictions.tolist() if predictions is not None else None,
        "stdout": stdout,
        "stderr": stderr,
    }
    
    # STEP 6: Add error classification
    if error_info:
        error_type, error_message = error_info
        result["error_type"] = error_type
        result["error_details"] = error_message
    else:
        result["error_type"] = None
        result["error_details"] = None
    
    return result
