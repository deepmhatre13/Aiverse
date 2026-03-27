#!/usr/bin/env python3
"""
ML Code Evaluation Runner — Secure Sandbox Environment

This script:
1. Loads datasets (train, test, hidden_test)
2. Imports and validates user code in a restricted sandbox
3. Executes train_and_predict function
4. Calculates metrics
5. Returns JSON result

Required user function signature:
    def train_and_predict(X_train, y_train, X_test):
        # All imports must be inside the function
        # Return predictions array
        pass

Allowed modules: numpy, pandas, sklearn, math
Blocked: os, sys, subprocess, socket, file I/O, network access
"""

import sys
import json
import argparse
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error

# ⭐ CRITICAL: Capture the real __import__ BEFORE overriding __builtins__
_real_import = __builtins__.__import__ if isinstance(__builtins__, dict) else __builtins__.__import__


def load_dataset(path, target_column):
    """Load CSV and split into features and target."""
    df = pd.read_csv(path)
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset")
    
    X = df.drop(columns=[target_column])
    y = df[target_column]
    return X, y


def calculate_metric(y_true, y_pred, metric):
    """Calculate the specified metric."""
    if metric == 'accuracy':
        return accuracy_score(y_true, y_pred)
    elif metric == 'f1':
        return f1_score(y_true, y_pred, average='weighted')
    elif metric == 'rmse':
        return np.sqrt(mean_squared_error(y_true, y_pred))
    else:
        raise ValueError(f"Unknown metric: {metric}")


# ========== SANDBOX: Import Whitelist ========== #

# Root modules allowed for import
# All sklearn submodules are allowed if root is sklearn
ALLOWED_ROOT_MODULES = {
    "numpy",
    "pandas", 
    "sklearn",
    "math",
}

# Explicitly blocked modules (security-critical)
BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "builtins",
    "importlib",
    "pickle",
    "shelve",
    "marshal",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "smtplib",
    "telnetlib",
    "code",
    "codeop",
    "gc",
    "__builtin__",
}

def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Wrapper around __import__ that only allows whitelisted modules.
    
    Security model:
    - Only numpy, pandas, sklearn, math root modules allowed
    - All sklearn submodules (sklearn.*) are permitted
    - Explicitly blocked modules raise ImportError
    - Unknown modules raise ImportError
    
    Args:
        name: Module name (e.g., "numpy", "sklearn.linear_model")
        globals, locals, fromlist, level: Passed to __import__
    
    Returns:
        Module object if whitelisted, raises ImportError otherwise
    """
    # Get the root module (e.g., "sklearn" from "sklearn.linear_model")
    root = name.split(".")[0]
    
    # Check if explicitly blocked
    if root in BLOCKED_MODULES or name in BLOCKED_MODULES:
        raise ImportError(
            f"Module '{name}' is blocked for security reasons. "
            f"Allowed modules: numpy, pandas, sklearn, math"
        )
    
    # Check if root module is allowed
    if root not in ALLOWED_ROOT_MODULES:
        raise ImportError(
            f"Module '{root}' is not allowed. "
            f"Allowed modules: numpy, pandas, sklearn, math"
        )
    
    # Call the real __import__ to load the module
    return _real_import(name, globals, locals, fromlist, level)


def load_user_code_safely(path):
    """
    Execute user code in a restricted sandbox.
    
    The sandbox:
    - Allows: numpy, pandas, sklearn imports
    - Blocks: os, sys, subprocess, file I/O, network, __import__ exploits
    - Provides: Basic builtins (len, range, print, etc.)
    
    Args:
        path: Path to user_code.py
        
    Returns:
        Dictionary of globals after exec (includes user functions)
    """
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # Minimal safe builtins for ML code
    safe_builtins = {
        "__import__": restricted_import,  # Our import whitelist
        "__name__": "__main__",
        "__builtins__": {},  # Prevent access to other builtins
        
        # Type constructors (numpy/pandas/sklearn need these)
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "type": type,
        "slice": slice,
        
        # Introspection (sklearn uses hasattr, isinstance)
        "hasattr": hasattr,
        "isinstance": isinstance,
        "callable": callable,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        
        # Math/logic (common in user code)
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "sorted": sorted,
        
        # I/O (print only, no file access)
        "print": print,
    }

    sandbox_globals = {
        "__builtins__": safe_builtins,
    }

    # Execute user code in the sandbox
    try:
        exec(code, sandbox_globals)
    except Exception as e:
        raise RuntimeError(f"Error executing user code: {e}")
    
    return sandbox_globals


def main():
    parser = argparse.ArgumentParser(description='Evaluate ML code submission')
    parser.add_argument('--train', required=True, help='Path to train.csv')
    parser.add_argument('--test', required=True, help='Path to test.csv')
    parser.add_argument('--hidden-test', required=True, help='Path to hidden_test.csv')
    parser.add_argument('--target', required=True, help='Target column name')
    parser.add_argument('--metric', required=True, choices=['accuracy', 'f1', 'rmse'], help='Evaluation metric')
    parser.add_argument('--user-code', required=True, help='Path to user_code.py')
    
    args = parser.parse_args()
    
    try:
        # Load datasets
        X_train, y_train = load_dataset(args.train, args.target)
        X_test, y_test = load_dataset(args.test, args.target)
        X_hidden, y_hidden = load_dataset(args.hidden_test, args.target)
        
        # Load and execute user code in sandbox
        sandbox_globals = load_user_code_safely(args.user_code)

        # Check that user defined train_and_predict
        if "train_and_predict" not in sandbox_globals:
            raise ValueError("User code must define function: train_and_predict(X_train, y_train, X_test)")

        train_and_predict = sandbox_globals["train_and_predict"]
        if not callable(train_and_predict):
            raise ValueError("train_and_predict must be callable")
        
        # Execute user code on public test set
        y_pred_public = train_and_predict(X_train, y_train, X_test)
        
        # Validate output shape
        if len(y_pred_public) != len(y_test):
            raise ValueError(f"Prediction length mismatch: expected {len(y_test)}, got {len(y_pred_public)}")
        
        # Calculate public score
        public_score = calculate_metric(y_test, y_pred_public, args.metric)
        
        # Execute user code on hidden test set
        y_pred_hidden = train_and_predict(X_train, y_train, X_hidden)
        
        # Validate output shape
        if len(y_pred_hidden) != len(y_hidden):
            raise ValueError(f"Prediction length mismatch: expected {len(y_hidden)}, got {len(y_pred_hidden)}")
        
        # Calculate private score
        private_score = calculate_metric(y_hidden, y_pred_hidden, args.metric)
        
        # Return success result
        result = {
            'status': 'success',
            'public_score': float(public_score),
            'private_score': float(private_score),
        }
        
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        # Return error result
        result = {
            'status': 'error',
            'error': str(e),
        }
        print(json.dumps(result))
        sys.exit(1)


if __name__ == '__main__':
    main()