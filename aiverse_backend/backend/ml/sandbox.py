"""
Safe code execution sandbox.

CRITICAL DESIGN: Imports ARE ALLOWED but strictly validated.
- Only numpy, pandas, sklearn allowed
- All other imports blocked at AST level (before execution)
- File I/O, network, os/sys forbidden

Code is validated BEFORE execution by validators.validate_imports().
This sandbox is the second layer of defense.
"""

import sys
import io
import signal
import time
from typing import Optional, Tuple
import numpy as np
import pandas as pd

# Memory tracking (optional, graceful fallback if psutil not available)
try:
    import psutil
    import os
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Import ML models for direct use (users can also import)
from sklearn.linear_model import (
    LogisticRegression, LinearRegression, Ridge, Lasso, ElasticNet,
    SGDClassifier, SGDRegressor
)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor
)
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB, MultinomialNB
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    PolynomialFeatures, LabelEncoder, OneHotEncoder
)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    mean_squared_error, mean_absolute_error, r2_score
)


class TimeoutException(Exception):
    """Raised when code execution exceeds timeout."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Code execution exceeded 5-second timeout")


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024  # Convert bytes to MB
    return 0.0


# ========== RESTRICTED IMPORT SYSTEM ========== #

# Capture the real __import__ BEFORE any sandbox override
_real_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

# Root modules that ARE allowed to be imported
ALLOWED_ROOT_MODULES = frozenset({
    'numpy',
    'pandas',
    'sklearn',
    'math',
    'np',   # alias
    'pd',   # alias
})

# Full module paths that are explicitly allowed (documentation)
ALLOWED_IMPORT_MODULES = frozenset({
    'numpy',
    'pandas',
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
    'sklearn.base',
    'sklearn.utils',
    'math',
})

# Explicitly blocked modules (security critical)
BLOCKED_MODULES = frozenset({
    'os', 'sys', 'subprocess', 'shutil', 'pathlib',
    'socket', 'requests', 'urllib', 'http',
    'joblib', 'pickle', 'dill', 'shelve', 'marshal',
    'builtins', '__builtin__', 'importlib',
    'ctypes', 'multiprocessing', 'threading', 'asyncio',
    'ftplib', 'smtplib', 'telnetlib',
    'code', 'codeop', 'gc',
})


def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Restricted __import__ that only allows numpy, pandas, sklearn, and math.
    
    Security model:
    - Only whitelisted root modules allowed
    - Explicitly blocked modules raise ImportError
    - Unknown modules raise ImportError
    
    Args:
        name: Module name (e.g., "numpy", "sklearn.linear_model")
        globals, locals, fromlist, level: Passed to real __import__
    
    Returns:
        Module object if allowed
        
    Raises:
        ImportError: If module is not in allowlist or is blocked
    """
    # Get the root module (e.g., "sklearn" from "sklearn.linear_model")
    root_module = name.split('.')[0]
    
    # Check if explicitly blocked
    if root_module in BLOCKED_MODULES or name in BLOCKED_MODULES:
        raise ImportError(
            f"Module '{name}' is blocked for security reasons.\n"
            f"Only numpy, pandas, sklearn, and math are permitted."
        )
    
    # Check if root module is allowed
    if root_module not in ALLOWED_ROOT_MODULES:
        raise ImportError(
            f"Module '{name}' is not allowed in this sandbox.\n"
            f"Only numpy, pandas, sklearn, and math are permitted.\n"
            f"Forbidden: os, sys, subprocess, socket, requests, etc."
        )
    
    # Use the captured real import
    return _real_import(name, globals, locals, fromlist, level)


def execute_user_code(
    user_code: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    timeout_seconds: int = 5
) -> Tuple[Optional[np.ndarray], float, float]:
    """
    Execute user code safely in isolated namespace with performance tracking.
    
    CRITICAL RULES:
    1. Imports are VALIDATED by AST before execution (validate_imports() called first)
    2. Only numpy, pandas, sklearn allowed
    3. File I/O, network, os/sys blocked at import validation level
    4. Takes exactly 3 arguments: X_train, y_train, X_test
    5. Must return predictions with shape (len(X_test),)
    
    Args:
        user_code: Python code string with train_and_predict function
        X_train: Training features
        y_train: Training labels
        X_test: Test features to predict on
        timeout_seconds: Execution timeout in seconds
    
    Returns:
        Tuple of:
        - Predictions from user's train_and_predict function (1D array)
        - Latency in milliseconds
        - Memory usage in MB (peak during execution)
    
    Raises:
        ValueError: If execution fails
        TimeoutException: If execution exceeds timeout
    """
    
    # STEP 1: Build safe globals with ML objects pre-injected
    # (users can also import these, but pre-injection allows direct use)
    safe_globals = {
        '__builtins__': {
            # CRITICAL: Allow restricted imports inside user code
            '__import__': restricted_import,
            
            # Allow only safe Python builtins
            'print': print,
            'len': len,
            'range': range,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'type': type,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'min': min,
            'max': max,
            'sum': sum,
            'abs': abs,
            'round': round,
            'pow': pow,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'object': object,
            'slice': slice,
            'reversed': reversed,
            'any': any,
            'all': all,
            
            # Exceptions that user code might need
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'AttributeError': AttributeError,
            'RuntimeError': RuntimeError,
            'Exception': Exception,
            'StopIteration': StopIteration,
            
            # None and boolean constants
            'None': None,
            'True': True,
            'False': False,
        },
        # NumPy and Pandas (pre-injected for ease of use)
        'np': np,
        'numpy': np,
        'pd': pd,
        'pandas': pd,
        
        # Scikit-learn: Classification models
        'LogisticRegression': LogisticRegression,
        'SGDClassifier': SGDClassifier,
        'DecisionTreeClassifier': DecisionTreeClassifier,
        'RandomForestClassifier': RandomForestClassifier,
        'GradientBoostingClassifier': GradientBoostingClassifier,
        'AdaBoostClassifier': AdaBoostClassifier,
        'SVC': SVC,
        'KNeighborsClassifier': KNeighborsClassifier,
        'GaussianNB': GaussianNB,
        'MultinomialNB': MultinomialNB,
        
        # Scikit-learn: Regression models
        'LinearRegression': LinearRegression,
        'Ridge': Ridge,
        'Lasso': Lasso,
        'ElasticNet': ElasticNet,
        'SGDRegressor': SGDRegressor,
        'DecisionTreeRegressor': DecisionTreeRegressor,
        'RandomForestRegressor': RandomForestRegressor,
        'GradientBoostingRegressor': GradientBoostingRegressor,
        'AdaBoostRegressor': AdaBoostRegressor,
        'SVR': SVR,
        'KNeighborsRegressor': KNeighborsRegressor,
        
        # Scikit-learn: Preprocessing
        'StandardScaler': StandardScaler,
        'MinMaxScaler': MinMaxScaler,
        'RobustScaler': RobustScaler,
        'PolynomialFeatures': PolynomialFeatures,
        'LabelEncoder': LabelEncoder,
        'OneHotEncoder': OneHotEncoder,
        
        # Scikit-learn: Pipeline
        'Pipeline': Pipeline,
        'make_pipeline': make_pipeline,
        
        # Scikit-learn: Metrics
        'accuracy_score': accuracy_score,
        'f1_score': f1_score,
        'precision_score': precision_score,
        'recall_score': recall_score,
        'mean_squared_error': mean_squared_error,
        'mean_absolute_error': mean_absolute_error,
        'r2_score': r2_score,
    }
    
    # STEP 2: Namespace for user code execution
    safe_locals = {
        'X_train': X_train,
        'y_train': y_train,
        'X_test': X_test,
    }
    
    # STEP 3: Capture stdout/stderr (suppress output)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    # Track memory before execution
    memory_before = get_memory_usage_mb()
    peak_memory = memory_before
    
    try:
        # Set timeout (Unix/Linux only; Windows will skip)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        # STEP 4: Execute user code in isolated namespace
        # CRITICAL: Code has already been validated for imports by validate_imports()
        exec_start = time.time()
        try:
            exec(user_code, safe_globals, safe_locals)
        except TimeoutException:
            raise ValueError("Code execution exceeded 5-second timeout")
        except SyntaxError as e:
            raise ValueError(f"Syntax error in code: {str(e)}")
        except Exception as e:
            # Re-raise for processing below
            raise
        
        # STEP 5: Retrieve train_and_predict function
        train_and_predict = safe_locals.get('train_and_predict')
        if train_and_predict is None:
            raise ValueError(
                "Code must define function: def train_and_predict(X_train, y_train, X_test)"
            )
        
        if not callable(train_and_predict):
            raise ValueError(
                "Code must define callable function: train_and_predict. "
                "Did you write def train_and_predict(...) correctly?"
            )
        
        # STEP 6: Call the function with exact 3 arguments and measure inference latency
        inference_start = time.time()
        try:
            predictions = train_and_predict(X_train, y_train, X_test)
        except TypeError as e:
            if "arguments" in str(e):
                raise ValueError(
                    "train_and_predict() must accept exactly 3 arguments: "
                    "X_train, y_train, X_test"
                )
            raise
        inference_end = time.time()
        
        # Calculate latency (inference time only, in milliseconds)
        latency_ms = (inference_end - inference_start) * 1000.0
        
        # Track peak memory during execution
        memory_after = get_memory_usage_mb()
        peak_memory = max(peak_memory, memory_after)
        memory_used_mb = max(0.0, peak_memory - memory_before)
        
        # Clear timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
        
        return predictions, latency_ms, memory_used_mb
    
    except Exception as e:
        # Wrap any exception as ValueError with clear message
        if isinstance(e, ValueError):
            raise  # Re-raise ValueError as-is (already clear)
        else:
            raise ValueError(f"{type(e).__name__}: {str(e)}")
    
    finally:
        # Clear timeout
        if hasattr(signal, 'SIGALRM'):
            try:
                signal.alarm(0)
            except:
                pass
        
        # Restore stdout/stderr
        sys.stdout = old_stdout
        sys.stderr = old_stderr
