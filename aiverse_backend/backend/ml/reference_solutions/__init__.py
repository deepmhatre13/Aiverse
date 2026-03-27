"""
Reference Solutions Module — Backend-Only, Never Exposed to Users

This module contains:
1. Reference solution file loader
2. Reference solution runner (admin only)
3. Threshold calibration utilities

CRITICAL SECURITY RULES:
- Reference solutions are NEVER serialized to API responses
- Reference solutions are NEVER logged
- Reference solutions are NEVER visible in frontend
- Reference solutions are ONLY used for:
  - Calibrating problem thresholds
  - Verifying metric correctness
  - Internal validation by admins

File structure:
    ml/reference_solutions/
        __init__.py                           # This file
        runner.py                             # Runner utility
        solutions/
            linear_binary_classification.py   # Problem-specific solution
            regression_fundamentals.py        # Problem-specific solution
            ...
"""

from .runner import (
    run_reference_solution,
    validate_threshold,
    get_reference_score,
    list_available_solutions,
)

__all__ = [
    'run_reference_solution',
    'validate_threshold', 
    'get_reference_score',
    'list_available_solutions',
]
