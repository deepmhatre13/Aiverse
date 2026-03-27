"""
Dataset Evaluation Framework for ML Problems

Defines the structure and execution logic for evaluating user submissions.
Each problem has:
- Public dataset splits (shown when user clicks "Evaluate")
- Private dataset splits (shown after "Submit")
"""

from dataclasses import dataclass
from typing import Literal, Tuple, List, Optional, Any, Dict
import numpy as np
from sklearn.datasets import load_iris, load_breast_cancer, load_digits, load_wine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error
import pandas as pd
import os


@dataclass
class TestCase:
    """
    Single evaluation dataset split for checking model performance.
    
    Attributes:
        name: Human-readable evaluation name
        X_train, y_train: Training data
        X_test, y_test: Test data for evaluation
        metric: How to evaluate (accuracy, f1, rmse, etc)
        threshold: Minimum score required to pass (0-1 for accuracy, 0-100 for rmse)
    """
    
    name: str
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    metric: Literal["accuracy", "f1", "rmse", "mae", "r2"]
    threshold: float = 0.5  # Default: pass if >= 50% accuracy
    
    def evaluate(self, predictions: np.ndarray) -> Dict[str, Any]:
        """
        Evaluate predictions with FAIR ML validation logic.
        
        This method:
        1. Converts various input types (list, pandas, etc) to numpy
        2. Validates shape (allows 2D single-column arrays)
        3. Uses metric-specific evaluation (with type-aware handling)
        4. Returns clear pass/fail decision
        
        Returns:
            {
                "passed": bool,
                "score": float,
                "expected_shape": tuple,
                "actual_shape": tuple,
                "error": Optional[str]
            }
        """
        
        try:
            # ====== STEP 1: TYPE CONVERSION ======
            # Convert various input types to numpy array
            if isinstance(predictions, (list, tuple)):
                predictions = np.asarray(predictions, dtype=np.float32)
            elif hasattr(predictions, 'to_numpy'):  # pandas Series/DataFrame
                predictions = predictions.to_numpy().flatten()
            elif not isinstance(predictions, np.ndarray):
                predictions = np.asarray(predictions)
            
            # Handle 2D arrays with single column (squeeze to 1D)
            if predictions.ndim == 2 and predictions.shape[1] == 1:
                predictions = predictions.squeeze()
            
            # ====== STEP 2: SHAPE VALIDATION ======
            if predictions.shape[0] != self.y_test.shape[0]:
                return {
                    "passed": False,
                    "score": 0.0,
                    "expected_shape": (self.y_test.shape[0],),
                    "actual_shape": tuple(predictions.shape),
                    "error": f"Output shape mismatch: expected ({self.y_test.shape[0]},), got {tuple(predictions.shape)}"
                }
            
            # ====== STEP 3: METRIC-SPECIFIC EVALUATION ======
            
            if self.metric == "accuracy":
                # For classification: predictions should be class labels (0, 1, 2, ...)
                # But user might return probabilities; we need smart type detection
                
                # Check if predictions look like probabilities (floats in [0, 1])
                if predictions.dtype != np.integer and predictions.min() >= -0.01 and predictions.max() <= 1.01:
                    # Likely probabilities; convert based on number of classes
                    n_classes = len(np.unique(self.y_test))
                    if n_classes == 2:
                        # Binary classification: threshold at 0.5
                        predicted_labels = (predictions > 0.5).astype(int)
                    else:
                        # Multiclass: this API shouldn't return probabilities
                        # But handle gracefully by rounding
                        predicted_labels = np.round(predictions).astype(int)
                else:
                    # Already class labels; use as-is
                    predicted_labels = np.round(predictions).astype(int)
                
                score = accuracy_score(self.y_test, predicted_labels)
            
            elif self.metric == "f1":
                # F1 score (classification)
                if predictions.dtype != np.integer and predictions.min() >= -0.01 and predictions.max() <= 1.01:
                    n_classes = len(np.unique(self.y_test))
                    if n_classes == 2:
                        predicted_labels = (predictions > 0.5).astype(int)
                    else:
                        predicted_labels = np.round(predictions).astype(int)
                else:
                    predicted_labels = np.round(predictions).astype(int)
                
                score = f1_score(self.y_test, predicted_labels, average='weighted', zero_division=0)
            
            elif self.metric == "rmse":
                # RMSE (regression): continuous predictions
                # Use predictions as-is
                score = np.sqrt(mean_squared_error(self.y_test, predictions))
            
            elif self.metric == "mae":
                # Mean Absolute Error (regression)
                score = np.mean(np.abs(self.y_test - predictions))
            
            elif self.metric == "r2":
                # R² score (regression)
                ss_res = np.sum((self.y_test - predictions) ** 2)
                ss_tot = np.sum((self.y_test - np.mean(self.y_test)) ** 2)
                score = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
            
            else:
                return {
                    "passed": False,
                    "score": 0.0,
                    "error": f"Unknown metric: {self.metric}"
                }
            
            # ====== STEP 4: THRESHOLD COMPARISON ======
            
            if self.metric in ["rmse", "mae"]:
                # For error metrics: lower is better
                passed = score <= self.threshold
            else:
                # For accuracy metrics: higher is better
                passed = score >= self.threshold
            
            # ====== STEP 5: RETURN RESULT ======
            
            return {
                "passed": passed,
                "score": float(score),
                "expected_shape": (self.y_test.shape[0],),
                "actual_shape": tuple(predictions.shape),
                "error": None
            }
        
        except Exception as e:
            import traceback
            return {
                "passed": False,
                "score": 0.0,
                "error": f"Evaluation error: {str(e)}\n{traceback.format_exc()}"
            }


class ProblemTestSuite:
    """
    Collection of dataset splits for a specific problem.
    
    Manages public evaluation splits (shown on "Evaluate") and private evaluation splits (after "Submit").
    """
    
    def __init__(self, problem_slug: str, public_tests: List[TestCase], private_tests: Optional[List[TestCase]] = None):
        self.problem_slug = problem_slug
        self.public_tests = public_tests
        self.private_tests = private_tests or []
    
    def run_public_tests(self, predict_func) -> Tuple[List[Dict], float]:
        """
        Run evaluation against all public dataset splits.
        
        Returns:
            (evaluation_results, avg_score)
        """
        results = []
        scores = []
        
        for test in self.public_tests:
            try:
                predictions = predict_func(test.X_train, test.y_train, test.X_test)
                result = test.evaluate(predictions)
                result["name"] = test.name
                results.append(result)
                if result["passed"]:
                    scores.append(1.0)
                else:
                    scores.append(result["score"])
            except Exception as e:
                results.append({
                    "name": test.name,
                    "passed": False,
                    "score": 0.0,
                    "error": str(e)
                })
                scores.append(0.0)
        
        avg_score = np.mean(scores) if scores else 0.0
        return results, float(avg_score)
    
    def run_private_tests(self, predict_func) -> Tuple[List[Dict], float]:
        """
        Run evaluation against all private dataset splits (for submission evaluation).
        
        Returns:
            (evaluation_results, avg_score)
        """
        results = []
        scores = []
        
        for test in self.private_tests:
            try:
                predictions = predict_func(test.X_train, test.y_train, test.X_test)
                result = test.evaluate(predictions)
                result["name"] = test.name
                results.append(result)
                if result["passed"]:
                    scores.append(1.0)
                else:
                    scores.append(result["score"])
            except Exception as e:
                results.append({
                    "name": test.name,
                    "passed": False,
                    "score": 0.0,
                    "error": str(e)
                })
                scores.append(0.0)
        
        avg_score = np.mean(scores) if scores else 0.0
        return results, float(avg_score)


# ============================================================================
# PROBLEM TEST SUITES - Define tests for each problem
# ============================================================================

def create_iris_tests() -> ProblemTestSuite:
    """
    Iris Species Classification
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: 0, 1, or 2 (class labels for iris species)
    - Metric: Accuracy (% correct predictions)
    
    Visible tests:
    - Validate that solution trains a basic classifier
    - Different train/test splits test generalization
    
    Hidden tests:
    - Additional train/test splits ensure robustness
    """
    
    iris = load_iris()
    X = iris.data
    y = iris.target
    
    # Preprocess: Standardize features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    # Any reasonable classifier should achieve ~70% accuracy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.70  # ← INCREASED: Fair baseline for any classifier
    ))
    
    # Public test 2: 70/30 split
    # Larger test set = harder to achieve high accuracy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=123, stratify=y
    )
    tests.append(TestCase(
        name="Test 2: Balanced split (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.68  # ← Slightly lower (larger test set)
    ))
    
    # Public test 3: 60/40 split
    # Smaller training set = even harder
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.4, random_state=456, stratify=y
    )
    tests.append(TestCase(
        name="Test 3: Limited data (60% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.65  # ← Lower (smaller training set)
    ))
    
    public_tests = tests
    
    # Private tests (additional evaluation, not shown to user until after submit)
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=789, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.68
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=321, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.65
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=654, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 3",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.66
    ))
    
    return ProblemTestSuite("iris-species-classification", public_tests, private_tests)


def create_breast_cancer_tests() -> ProblemTestSuite:
    """
    Breast Cancer Classification Problem
    
    Binary classification task.
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: 0 or 1 (class labels)
    - Metric: Accuracy (% correct predictions)
    
    Note: High-quality dataset (569 samples, 30 features)
    Any reasonable classifier should achieve >85% accuracy
    """
    
    bc = load_breast_cancer()
    X = bc.data
    y = bc.target
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.90  # ← Achievable with LogisticRegression
    ))
    
    # Public test 2: Larger test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=123, stratify=y
    )
    tests.append(TestCase(
        name="Test 2: Larger test set (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.88  # ← Slightly lower (larger test set)
    ))
    
    public_tests = tests
    
    # Private tests
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=789, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.90
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=321, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.87
    ))
    
    return ProblemTestSuite("breast-cancer-classification", public_tests, private_tests)


def create_spam_detection_tests() -> ProblemTestSuite:
    """
    Spam Detection - Binary Classification
    
    Uses breast cancer dataset as proxy (similar 2-class structure to spam detection).
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: 0 (ham) or 1 (spam)
    - Metric: F1 Score (balanced metric for imbalanced datasets)
    
    Note: F1 score is more appropriate than accuracy for imbalanced spam datasets
    """
    
    bc = load_breast_cancer()
    X = bc.data
    y = bc.target
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.85  # F1 score: achievable with LogisticRegression
    ))
    
    # Public test 2: Larger test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=123, stratify=y
    )
    tests.append(TestCase(
        name="Test 2: Larger test set (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.82  # Slightly lower (larger test set = more variation)
    ))
    
    public_tests = tests
    
    # Private tests
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=789, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.84
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=321, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.81
    ))
    
    return ProblemTestSuite("spam-detection", public_tests, private_tests)


def create_churn_prediction_tests() -> ProblemTestSuite:
    """
    Customer Churn Prediction - Binary Classification
    
    Uses breast cancer dataset as proxy (similar 2-class structure to churn data).
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: 0 (retained) or 1 (churned)
    - Metric: F1 Score (balanced metric, important for identifying churn)
    
    Note: F1 is preferred for identifying rare but important events (churn)
    """
    
    bc = load_breast_cancer()
    X = bc.data
    y = bc.target
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=111, stratify=y
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.85
    ))
    
    # Public test 2: Larger test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=222, stratify=y
    )
    tests.append(TestCase(
        name="Test 2: Larger test set (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.82
    ))
    
    public_tests = tests
    
    # Private tests
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=333, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.84
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=444, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="f1",
        threshold=0.81
    ))
    
    return ProblemTestSuite("customer-churn-prediction", public_tests, private_tests)


def create_credit_risk_tests() -> ProblemTestSuite:
    """
    Credit Risk Prediction - Binary Classification
    
    Uses breast cancer dataset as proxy (similar 2-class structure to credit risk).
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: 0 (no default) or 1 (default)
    - Metric: Accuracy (primary metric for credit decisions)
    
    Note: Breast cancer dataset has good feature quality and clear separation
    """
    
    bc = load_breast_cancer()
    X = bc.data
    y = bc.target
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=555, stratify=y
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.90
    ))
    
    # Public test 2: Larger test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=666, stratify=y
    )
    tests.append(TestCase(
        name="Test 2: Larger test set (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.88
    ))
    
    public_tests = tests
    
    # Private tests
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=777, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.89
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=888, stratify=y
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="accuracy",
        threshold=0.87
    ))
    
    return ProblemTestSuite("credit-risk-prediction", public_tests, private_tests)


def create_housing_price_tests() -> ProblemTestSuite:
    """
    House Price Prediction - Regression
    
    Uses load_digits dataset as proxy for regression (maps pixel intensity to digit).
    
    Contract:
    - Function: train_and_predict(X_train, y_train, X_test)
    - Returns: numpy array of shape (n_test_samples,)
    - Values: Predicted prices/values (floating point)
    - Metric: RMSE (Root Mean Squared Error - lower is better)
    
    Note: Regression metric requires different evaluation logic
    Digits dataset: ~1800 samples, 64 features (8x8 pixels), regression task
    """
    
    # Use digits dataset as regression proxy (pixel intensity prediction)
    digits = load_digits()
    X = digits.data
    y = digits.target.astype(np.float32)  # Convert to float for regression
    
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    tests = []
    
    # Public test 1: Standard 80/20 split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=999, 
    )
    tests.append(TestCase(
        name="Test 1: Standard split (80% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="rmse",
        threshold=1.5  # RMSE: lower is better, 1.5 is reasonable for housing
    ))
    
    # Public test 2: Larger test set
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=1111
    )
    tests.append(TestCase(
        name="Test 2: Larger test set (70% train)",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="rmse",
        threshold=1.6  # Slightly higher (larger test set = more variation)
    ))
    
    public_tests = tests
    
    # Private tests
    private_tests = []
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=2222
    )
    private_tests.append(TestCase(
        name="Private Test 1",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="rmse",
        threshold=1.55
    ))
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.35, random_state=3333
    )
    private_tests.append(TestCase(
        name="Private Test 2",
        X_train=X_train,
        y_train=y_train,
        X_test=X_test,
        y_test=y_test,
        metric="rmse",
        threshold=1.65
    ))
    
    return ProblemTestSuite("house-price-prediction", public_tests, private_tests)

# ============================================================================
# REGISTRY - Mapping from problem slug to test suite
# ============================================================================

PROBLEM_TEST_SUITES = {
    "iris-species-classification": create_iris_tests(),
    "iris-classification": create_iris_tests(),  # Alias for same tests
    "spam-detection": create_spam_detection_tests(),
    "customer-churn-prediction": create_churn_prediction_tests(),
    "credit-risk-prediction": create_credit_risk_tests(),
    "house-price-prediction": create_housing_price_tests(),
    "breast-cancer-classification": create_breast_cancer_tests(),
}


def get_test_suite(problem_slug: str) -> Optional[ProblemTestSuite]:
    """Get test suite for a problem by slug."""
    return PROBLEM_TEST_SUITES.get(problem_slug)
