"""
Code validation utilities.
Stateless validation functions for user code.

CRITICAL: 
- Imports ARE ALLOWED but strictly restricted
- Only numpy, pandas, sklearn, and math allowed
- File I/O, network, os/sys/subprocess forbidden
- Validates function contracts and signatures
"""

import ast
from typing import Optional, Set


# Allowed root modules for importing
ALLOWED_ROOT_MODULES = {
    'numpy', 'np',
    'pandas', 'pd',
    'sklearn',
    'math',
}

# Allowed full module names (for documentation and explicit validation)
ALLOWED_MODULES = {
    'numpy', 'np',
    'pandas', 'pd',
    'sklearn',
    'sklearn.linear_model',
    'sklearn.tree',
    'sklearn.ensemble',
    'sklearn.svm',
    'sklearn.neighbors',
    'sklearn.naive_bayes',
    'sklearn.preprocessing',
    'sklearn.pipeline',
    'sklearn.metrics',
    'sklearn.model_selection',
    'sklearn.impute',
    'sklearn.decomposition',
    'sklearn.cluster',
    'sklearn.feature_selection',
    'math',
}

# Forbidden modules that WILL NOT be allowed (security critical)
FORBIDDEN_MODULES = {
    'os', 'sys', 'subprocess', 'shutil', 'pathlib',
    'socket', 'requests', 'urllib', 'http',
    'joblib', 'pickle', 'dill', 'shelve', 'marshal',
    'open', '__import__', 'eval', 'exec',
    'builtins', '__builtin__', 'importlib',
    'ctypes', 'multiprocessing', 'threading', 'asyncio',
    'ftplib', 'smtplib', 'telnetlib',
    'code', 'codeop', 'gc',
}


def validate_code_not_empty(code: str) -> None:
    """Raise ValueError if code is empty or whitespace."""
    if not code or not code.strip():
        raise ValueError("Code cannot be empty. Please write some code.")


def validate_imports(code: str) -> None:
    """
    Validate imports: ONLY allowed inside train_and_predict function body.
    
    ✅ ALLOWED (inside function):
    def train_and_predict(X_train, y_train, X_test):
        import numpy as np
        from sklearn.linear_model import LogisticRegression
    
    ❌ FORBIDDEN (top-level):
    import numpy
    from sklearn import *
    
    Only numpy, pandas, sklearn allowed.
    File I/O, network, os/sys forbidden.
    
    Raises ValueError with clear guidance.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {str(e)}")
    
    # Find train_and_predict function
    train_and_predict_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "train_and_predict":
            train_and_predict_node = node
            break
    
    # Check for top-level imports (at module level, not inside function)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                raise ValueError(
                    f"Imports are only allowed inside train_and_predict().\n"
                    f"Top-level imports are disabled.\n"
                    f"Move 'import {module_name}' inside the function body."
                )
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or "."
            raise ValueError(
                f"Imports are only allowed inside train_and_predict().\n"
                f"Top-level imports are disabled.\n"
                f"Move 'from {module_name} import ...' inside the function body."
            )
    
    # Now check function-body imports (these are allowed, but only from safe modules)
    if train_and_predict_node:
        for node in ast.walk(train_and_predict_node):
            # Check imports inside the function
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    root_module = module_name.split('.')[0]
                    
                    # Check if forbidden
                    if root_module in FORBIDDEN_MODULES or module_name in FORBIDDEN_MODULES:
                        raise ValueError(
                            f"Module '{module_name}' is not allowed.\n"
                            f"Forbidden: os, sys, subprocess, socket, requests, pickle, joblib, file I/O\n"
                            f"Allowed: numpy, pandas, sklearn, math only"
                        )
                    
                    # Check if allowed
                    if root_module not in ALLOWED_ROOT_MODULES:
                        raise ValueError(
                            f"Module '{module_name}' is not allowed.\n"
                            f"Only available:\n"
                            f"- numpy\n"
                            f"- pandas\n"
                            f"- sklearn (all submodules)\n"
                            f"- math"
                        )
            
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module  # e.g., 'sklearn.linear_model'
                
                if not module_name:
                    raise ValueError("Relative imports are not allowed")
                
                root_module = module_name.split('.')[0]
                
                # Check if forbidden
                if root_module in FORBIDDEN_MODULES or module_name in FORBIDDEN_MODULES:
                    raise ValueError(
                        f"Module '{module_name}' is not allowed.\n"
                        f"Forbidden: os, sys, subprocess, socket, requests, pickle, joblib"
                    )
                
                # Check if allowed
                if root_module not in ALLOWED_ROOT_MODULES:
                    raise ValueError(
                        f"Module '{module_name}' is not allowed.\n"
                        f"Only available:\n"
                        f"- numpy\n"
                        f"- pandas\n"
                        f"- sklearn (all submodules)\n"
                        f"- math"
                    )


def validate_function_exists(code: str, func_name: str = "train_and_predict") -> None:
    """Raise ValueError if required function not found in code."""
    if func_name not in code:
        raise ValueError(
            f"Code must define function: def {func_name}(X_train, y_train, X_test)"
        )


def validate_function_signature(
    code: str,
    func_name: str = "train_and_predict",
    expected_args: int = 3
) -> None:
    """
    Parse code with AST and validate function signature.
    Raise ValueError if signature is invalid.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {str(e)}")
    
    # Find function definition
    func_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            func_def = node
            break
    
    if not func_def:
        raise ValueError(
            f"Code must define function: def {func_name}(X_train, y_train, X_test)"
        )
    
    # Check argument count (strict: exactly 3)
    arg_count = len(func_def.args.args)
    if arg_count != expected_args:
        raise ValueError(
            f"{func_name}() expects exactly {expected_args} arguments, got {arg_count}"
        )


def validate_predictions(predictions, expected_len: int) -> None:
    """
    Raise ValueError if predictions are invalid shape/type.
    """
    if predictions is None:
        raise ValueError(
            "Function must return predictions (got None). "
            "Did you forget to add 'return predictions'?"
        )
    
    if not hasattr(predictions, '__len__'):
        raise ValueError(
            f"Predictions must be array-like (e.g., list or numpy array), "
            f"got {type(predictions).__name__}"
        )
    
    if len(predictions) != expected_len:
        raise ValueError(
            f"Expected {expected_len} predictions, got {len(predictions)}. "
            f"Check that X_test has {expected_len} samples."
        )

def validate_task_type(
    task_type: str,
    y_test,
    predictions
) -> None:
    """
    Validate that predictions match the task type.
    
    Classification: y_test should be integers, predictions should be integers (class labels)
    Regression: y_test should be floats, predictions can be floats or integers (but typically floats)
    
    Raises ValueError if there's a mismatch.
    """
    import numpy as np
    
    task_type = task_type.lower()
    
    # Convert to numpy arrays for easier validation
    y_test_arr = np.asarray(y_test)
    predictions_arr = np.asarray(predictions)
    
    if task_type == 'classification':
        # For classification, predictions should be integers (class indices)
        unique_pred = np.unique(predictions_arr)
        
        # Check if predictions look like continuous values (regression output)
        # If min/max differ by small amount with many unique values, likely regression
        if len(unique_pred) > 1:
            min_val = unique_pred.min()
            max_val = unique_pred.max()
            # If many unique values and they're not clearly integers, likely regression
            if len(unique_pred) > 10 and (max_val - min_val) < 100:
                # Check if values are close to integers
                if not np.allclose(predictions_arr, np.round(predictions_arr)):
                    raise ValueError(
                        f"Classification problem expects discrete class labels (integers like 0, 1, 2), "
                        f"but received continuous predictions. Did you return probabilities or "
                        f"continuous values instead of class labels? Use model.predict() not model.predict_proba()."
                    )
    
    elif task_type == 'regression':
        # For regression, predictions should be floats (continuous)
        # Check if predictions are suspiciously discrete (classification)
        unique_pred = np.unique(predictions_arr)
        
        if len(unique_pred) <= 5 and len(predictions_arr) > 10:
            # Very few unique values for many predictions = likely classification
            raise ValueError(
                f"Regression problem expects continuous numerical predictions (floats), "
                f"but your model returned only {len(unique_pred)} unique values. "
                f"This looks like a classification model. Are you using a regression model like "
                f"LinearRegression or RandomForestRegressor?"
            )