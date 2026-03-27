"""
Metric computation utilities.
Stateless metric evaluation functions.
"""

import numpy as np
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    mean_squared_error, mean_absolute_error, r2_score
)

# Metric direction helpers
HIGHER_IS_BETTER_METRICS = ["accuracy", "f1", "precision", "recall", "r2"]
LOWER_IS_BETTER_METRICS = ["rmse", "mae", "mse"]


def compute_metric(
    metric: str,
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> float:
    """
    Compute evaluation metric.
    
    Supported metrics:
    - Classification: accuracy, f1, precision, recall
    - Regression: mse, mae, rmse, r2
    """
    metric = metric.lower().strip()
    
    # Classification metrics
    if metric == "accuracy":
        return accuracy_score(y_true, y_pred)
    elif metric == "f1":
        # Handle both binary and multi-class
        if len(np.unique(y_true)) == 2:
            return f1_score(y_true, y_pred, average='binary')
        else:
            return f1_score(y_true, y_pred, average='weighted')
    elif metric == "precision":
        return precision_score(y_true, y_pred, average='weighted', zero_division=0)
    elif metric == "recall":
        return recall_score(y_true, y_pred, average='weighted', zero_division=0)
    
    # Regression metrics
    elif metric == "mse":
        return mean_squared_error(y_true, y_pred)
    elif metric == "mae":
        return mean_absolute_error(y_true, y_pred)
    elif metric == "rmse":
        return np.sqrt(mean_squared_error(y_true, y_pred))
    elif metric == "r2":
        return r2_score(y_true, y_pred)
    
    else:
        raise ValueError(f"Unknown metric: {metric}")
