"""
API Validation and Compatibility Layer for ML Code Execution

Enforces scikit-learn API compatibility before code execution.
Detects deprecated/unsupported parameters and rejects them with clear errors.
"""

import ast
import re
from typing import List, Tuple, Optional, Dict


class DeprecatedParameter:
    """Definition of a deprecated parameter."""
    
    def __init__(self, class_name: str, param_name: str, removed_version: str, fix: str):
        self.class_name = class_name
        self.param_name = param_name
        self.removed_version = removed_version
        self.fix = fix


# ============================================================================
# SKLEARN API COMPATIBILITY MAP
# ============================================================================
# Maps class_name -> [deprecated parameters]
# Updated for sklearn >= 1.6 where multi_class was removed
DEPRECATED_SKLEARN_PARAMS = {
    'LogisticRegression': [
        DeprecatedParameter(
            'LogisticRegression',
            'multi_class',
            '1.6',
            "Remove 'multi_class' parameter. Modern scikit-learn (>= 1.6) removed this. "
            "Replace: LogisticRegression(multi_class='multinomial') with LogisticRegression()"
        ),
    ],
    # Add more as needed for newer sklearn versions
}


class SKLearnAPIValidator:
    """Validates user code for sklearn API compliance."""
    
    def __init__(self):
        self.errors: List[Tuple[str, str]] = []  # [(error_type, message), ...]
    
    def validate(self, code: str) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Validate code for deprecated sklearn parameters.
        
        Returns:
            (is_valid, errors)
            - is_valid: True if no deprecated params detected
            - errors: List of (error_type, message) tuples
        """
        self.errors = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # Syntax errors are runtime errors, not validation errors
            return True, []
        
        # Walk the AST and find function calls
        self._check_function_calls(tree)
        
        return len(self.errors) == 0, self.errors
    
    def _check_function_calls(self, node):
        """Recursively check all function calls for deprecated parameters."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self._check_call(child)
    
    def _check_call(self, call_node: ast.Call):
        """Check a single function call for deprecated parameters."""
        # Get the function name
        func_name = self._get_func_name(call_node.func)
        
        if not func_name:
            return
        
        # Check if this class has deprecated parameters
        if func_name not in DEPRECATED_SKLEARN_PARAMS:
            return
        
        # Get the deprecated parameters for this class
        deprecated_params = DEPRECATED_SKLEARN_PARAMS[func_name]
        
        # Get the keyword arguments in this call
        keywords = {kw.arg: kw.value for kw in call_node.keywords if kw.arg}
        
        # Check each deprecated parameter
        for deprecated in deprecated_params:
            if deprecated.param_name in keywords:
                error_msg = (
                    f"Unsupported argument '{deprecated.param_name}' in {deprecated.class_name}(). "
                    f"This parameter was removed in scikit-learn {deprecated.removed_version}. "
                    f"Fix: {deprecated.fix}"
                )
                self.errors.append(("USER_ERROR", error_msg))
    
    def _get_func_name(self, func_node) -> Optional[str]:
        """Extract function name from AST node."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            # For cases like sklearn.linear_model.LogisticRegression
            return func_node.attr
        return None


class APICompatibilityLayer:
    """High-level API compatibility checking."""
    
    @staticmethod
    def check_code(code: str) -> Tuple[bool, Optional[str]]:
        """
        Check code for API compatibility issues.
        
        Returns:
            (is_compatible, error_message)
            - is_compatible: True if code is safe to execute
            - error_message: User-friendly error if not compatible
        """
        validator = SKLearnAPIValidator()
        is_valid, errors = validator.validate(code)
        
        if not is_valid:
            # Format errors for user display
            error_lines = [f"  • {msg}" for _, msg in errors]
            error_message = (
                f"API Compatibility Error:\n"
                + "\n".join(error_lines)
            )
            return False, error_message
        
        return True, None


# ============================================================================
# SKLEARN VERSION INFO
# ============================================================================

def get_sklearn_version() -> str:
    """Get installed scikit-learn version."""
    import sklearn
    return sklearn.__version__


def check_sklearn_version() -> Tuple[str, bool]:
    """
    Check if sklearn version is supported.
    
    Returns:
        (version, is_supported)
        - version: Installed sklearn version
        - is_supported: True if version is in supported range
    """
    version = get_sklearn_version()
    
    # Check if version is 1.0 or newer (where multi_class was removed)
    try:
        major, minor = version.split('.')[:2]
        major = int(major)
        
        # Support 0.24.x to 1.3.x
        if major == 0:
            return version, True  # 0.24.x
        elif major == 1:
            return version, True  # 1.0.x, 1.1.x, etc.
        else:
            return version, False  # Unknown future version
    except:
        return version, True  # Can't parse, assume compatible


# ============================================================================
# SKLEARN API FIX SUGGESTIONS
# ============================================================================

class APIFixSuggestion:
    """Provides suggestions to fix deprecated API usage."""
    
    FIXES = {
        'multi_class': {
            'problem': "LogisticRegression no longer accepts 'multi_class' parameter",
            'solution': "Remove the 'multi_class' argument. Modern scikit-learn handles multi-class classification automatically.",
            'example_before': "clf = LogisticRegression(multi_class='multinomial')",
            'example_after': "clf = LogisticRegression()",
        },
    }
    
    @staticmethod
    def get_fix(param_name: str) -> Optional[Dict[str, str]]:
        """Get fix suggestion for a parameter."""
        return APIFixSuggestion.FIXES.get(param_name)
