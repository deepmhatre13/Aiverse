"""
Canonical concept -> prerequisite edge map.

Neutral module shared by ``learner.services.prerequisites`` and
``recommendations.services``. Keeping this constant here (instead of inside
``recommendations.services``) avoids the circular import between those two
modules.

Dependency graph:

    prerequisite_map.py
        |--------+
        v        v
   prerequisites  recommendations
   (learner)       (recommendations)
"""

# Prerequisite map: if weak in X, recommend Y first
PREREQUISITE_MAP = {
    'gradient_descent': ['statistics', 'linear_algebra'],
    'neural_networks': ['gradient_descent', 'linear_algebra', 'regression'],
    'regression': ['statistics', 'linear_algebra', 'python_ml'],
    'classification': ['regression', 'statistics'],
    'cnn': ['neural_networks'],
    'rnn': ['neural_networks'],
    'transformers': ['rnn', 'neural_networks'],
    'pca': ['linear_algebra', 'statistics'],
    'svm': ['classification', 'linear_algebra'],
    'ensemble_learning': ['classification', 'regression'],
    'backpropagation': ['neural_networks', 'gradient_descent'],
}