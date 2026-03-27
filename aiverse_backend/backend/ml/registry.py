"""
ML Problems Registry — Production-Grade ML Evaluation Platform

18 real-world ML problems across 5 difficulty tiers:
- Easy (800 rating): Foundational ML concepts
- Medium (1200 rating): Applied data science
- Hard (1600 rating): Production ML engineering
- Expert (2000 rating): MLOps and system-level challenges

Central registry mapping problem slugs to definitions with:
- Messy dataset simulation
- Train/test/hidden split
- Metric-based evaluation
- Threshold enforcement
- Industrial constraints (latency, memory)
"""

import numpy as np
from sklearn.model_selection import train_test_split


class ProblemDefinition:
    """
    Immutable problem definition with dataset, metrics, thresholds, and constraints.

    Fields:
        slug: Unique URL-safe identifier
        title: Display name
        task_type: "classification" or "regression"
        default_metric: Primary metric for evaluation
        allowed_metrics: Metrics the user can select
        submission_threshold: Score required for ACCEPTED
        dataset_loader: Callable returning (X, y, metadata)
        description: Markdown problem statement
        difficulty: "easy" | "medium" | "hard" | "expert"
        difficulty_rating: ELO rating for the problem (800/1200/1600/2000)
        category: Problem domain category
        constraints: Dict of production constraints (max_latency_ms, max_memory_mb)
        hidden_test_ratio: Fraction of data reserved for hidden evaluation
        higher_is_better: Auto-calculated based on metric type
    """
    
    # Metrics where LOWER is better
    LOWER_IS_BETTER = {'rmse', 'mae', 'mse'}

    def __init__(
        self,
        slug: str,
        title: str,
        task_type: str,
        default_metric: str,
        allowed_metrics: list,
        submission_threshold: float,
        dataset_loader,
        description: str = "",
        difficulty: str = "easy",
        difficulty_rating: int = 800,
        category: str = "general",
        constraints: dict = None,
        hidden_test_ratio: float = 0.0,
    ):
        self.slug = slug
        self.title = title
        self.task_type = task_type
        self.default_metric = default_metric
        self.allowed_metrics = allowed_metrics
        self.submission_threshold = submission_threshold
        self._dataset_loader = dataset_loader
        self.description = description
        self.difficulty = difficulty
        self.difficulty_rating = difficulty_rating
        self.category = category
        self.constraints = constraints or {}
        self.hidden_test_ratio = hidden_test_ratio
        
        # Auto-calculate higher_is_better based on metric
        self.higher_is_better = default_metric.lower().strip() not in self.LOWER_IS_BETTER

    def load_full_dataset(self):
        """Load and return full dataset (before train/test split)."""
        return self._dataset_loader()

    def load_visible_dataset(self):
        """Load dataset and perform deterministic 80/20 split."""
        X, y, metadata = self.load_full_dataset()

        if self.task_type == "classification":
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=0.2,
                random_state=42,
                stratify=y
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=0.2,
                random_state=42
            )

        return X_train, y_train, X_test, y_test

    def load_hidden_dataset(self):
        """
        Load dataset with 3-way split: train / visible_test / hidden_test.
        Returns (X_train, y_train, X_visible_test, y_visible_test, X_hidden, y_hidden).
        """
        X, y, metadata = self.load_full_dataset()

        if self.hidden_test_ratio <= 0:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42,
                stratify=y if self.task_type == "classification" else None
            )
            return X_train, y_train, X_test, y_test, np.array([]), np.array([])

        # First split: train+visible vs hidden
        strat = y if self.task_type == "classification" else None
        X_main, X_hidden, y_main, y_hidden = train_test_split(
            X, y, test_size=self.hidden_test_ratio, random_state=99, stratify=strat
        )

        # Second split: train vs visible_test from main
        strat_main = y_main if self.task_type == "classification" else None
        X_train, X_vis_test, y_train, y_vis_test = train_test_split(
            X_main, y_main, test_size=0.2, random_state=42, stratify=strat_main
        )

        return X_train, y_train, X_vis_test, y_vis_test, X_hidden, y_hidden

    def to_dict(self):
        """Serialize to dict for API responses."""
        return {
            "slug": self.slug,
            "title": self.title,
            "task_type": self.task_type,
            "default_metric": self.default_metric,
            "allowed_metrics": self.allowed_metrics,
            "submission_threshold": self.submission_threshold,
            "difficulty": self.difficulty,
            "difficulty_rating": self.difficulty_rating,
            "category": self.category,
            "constraints": self.constraints,
            "has_hidden_tests": self.hidden_test_ratio > 0,
            "higher_is_better": self.higher_is_better,
        }


# ============================================================================
# PROBLEM 1: LINEAR BINARY CLASSIFICATION (EASY — 800)
# ============================================================================

def _load_linear_binary_dataset():
    np.random.seed(42)
    n_samples = 500
    n_features = 10
    X = np.random.normal(0, 1, (n_samples, n_features))
    decision_score = X.sum(axis=1) + np.random.normal(0, 0.5, n_samples)
    y = (decision_score > 0).astype(int)
    metadata = {
        "dataset_name": "linear_binary_classification",
        "num_samples": len(X),
        "num_features": X.shape[1],
        "features": [f"feature_{i}" for i in range(n_features)],
        "task_type": "classification",
        "class_balance": {"0": int(np.sum(y == 0)), "1": int(np.sum(y == 1))},
        "split_strategy": "80/20 stratified",
        "random_seed": 42,
    }
    return X, y, metadata


LINEAR_BINARY_DESCRIPTION = """# Linear Binary Classification

## Context

You are given a dataset with 10 numeric features and binary labels (0 or 1).
The classes are separable in feature space.

## Task

Train a classifier that achieves at least **80% accuracy** on the test set.

## Input Format

- `X_train`: Training features (400, 10) - numpy array
- `y_train`: Training labels (400,) - numpy array of 0s and 1s
- `X_test`: Test features (100, 10) - numpy array

## Output Format

Return predictions as a numpy array or list of length 100.
Each prediction must be 0 or 1.

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.80

## Constraints

- All imports must be inside the function body
- No file I/O or network access
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 2: REGRESSION FUNDAMENTALS (EASY — 800)
# ============================================================================

def _load_regression_fundamentals_dataset():
    np.random.seed(42)
    n_samples = 100
    X = np.random.normal(0, 2, (n_samples, 2))
    y = 3 * X[:, 0] + 2 * X[:, 1] + np.random.normal(0, 1, n_samples)
    metadata = {
        "dataset_name": "regression_fundamentals",
        "num_samples": len(X),
        "num_features": X.shape[1],
        "features": ["feature_1", "feature_2"],
        "task_type": "regression",
        "formula": "y = 3*x1 + 2*x2 + noise",
        "split_strategy": "80/20 random",
        "random_seed": 42,
    }
    return X, y, metadata


REGRESSION_FUNDAMENTALS_DESCRIPTION = """# Regression Fundamentals

## Context

A dataset with 2 numeric features and continuous target values.
The relationship between features and target is linear.

## Task

Train a regression model achieving **RMSE <= 20.0** on the test set.

## Input Format

- `X_train`: Training features (80, 2) - numpy array
- `y_train`: Training targets (80,) - numpy array of floats
- `X_test`: Test features (20, 2) - numpy array

## Output Format

Return predictions as a numpy array or list of length 20.
Predictions should be continuous float values.

## Evaluation

- **Metric**: RMSE (lower is better)
- **Threshold**: <= 20.0

## Constraints

- All imports must be inside the function body
- Return float predictions, not class labels
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 3: IMBALANCED CLASSIFICATION (EASY — 800)
# ============================================================================

def _load_imbalanced_classification_dataset():
    np.random.seed(42)
    n_samples = 1000
    n_pos = int(n_samples * 0.1)
    n_neg = n_samples - n_pos
    X_neg = np.random.normal([-2]*5, 1.5, (n_neg, 5))
    y_neg = np.zeros(n_neg, dtype=int)
    X_pos = np.random.normal([2]*5, 1.5, (n_pos, 5))
    y_pos = np.ones(n_pos, dtype=int)
    X = np.vstack([X_neg, X_pos])
    y = np.hstack([y_neg, y_pos])
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]
    metadata = {
        "dataset_name": "imbalanced_classification",
        "num_samples": len(X),
        "num_features": X.shape[1],
        "features": [f"feature_{i+1}" for i in range(5)],
        "task_type": "classification",
        "class_balance": {"0": int(np.sum(y == 0)), "1": int(np.sum(y == 1))},
        "imbalance_ratio": "90:10",
        "split_strategy": "80/20 stratified",
        "random_seed": 42,
    }
    return X, y, metadata


IMBALANCED_CLASSIFICATION_DESCRIPTION = """# Imbalanced Classification (F1 Score)

## Context

Binary classification with significant class imbalance (90/10 split).
Standard accuracy is misleading — a naive classifier achieves 90% accuracy by predicting all zeros.

## Task

Achieve **F1 >= 0.60** on the test set.

## Input Format

- `X_train`: Training features (800, 5) - numpy array
- `y_train`: Training labels (800,) - 90% class 0, 10% class 1
- `X_test`: Test features (200, 5) - numpy array

## Output Format

Return predictions as a numpy array or list of length 200.
Each prediction must be 0 or 1.

## Evaluation

- **Metric**: F1 Score (higher is better)
- **Threshold**: >= 0.60

## Constraints

- All imports must be inside the function body
- Handle the class imbalance appropriately
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 4: CREDIT RISK MODELING (MEDIUM — 1200)
# ============================================================================

def _load_credit_risk_dataset():
    np.random.seed(101)
    n = 2000

    age = np.random.normal(40, 12, n).clip(18, 75)
    income = np.random.lognormal(10.5, 0.8, n)
    debt_ratio = np.random.beta(2, 5, n)
    credit_history_years = np.random.exponential(8, n).clip(0, 40)
    num_credit_lines = np.random.poisson(4, n)
    late_payments = np.random.poisson(1.5, n)
    employment_years = np.random.exponential(5, n).clip(0, 35)
    loan_amount = np.random.lognormal(9.5, 1.0, n)
    savings_ratio = np.random.beta(2, 8, n)
    num_dependents = np.random.poisson(1.2, n)

    # Inject missing values (messy data)
    missing_mask = np.random.random((n, 10)) < 0.05
    X = np.column_stack([
        age, income, debt_ratio, credit_history_years, num_credit_lines,
        late_payments, employment_years, loan_amount, savings_ratio, num_dependents
    ])
    X = X.astype(float)
    X[missing_mask] = np.nan

    # Default probability based on risk factors
    risk_score = (
        -0.03 * age + 0.00001 * loan_amount - 0.000005 * income
        + 2.0 * debt_ratio + 0.15 * late_payments
        - 0.05 * credit_history_years - 0.04 * employment_years
        - 1.5 * savings_ratio + 0.1 * num_dependents
        + np.random.normal(0, 0.5, n)
    )
    prob_default = 1 / (1 + np.exp(-risk_score))
    y = (prob_default > 0.5).astype(int)

    metadata = {
        "dataset_name": "credit_risk",
        "num_samples": n,
        "num_features": 10,
        "features": ["age", "income", "debt_ratio", "credit_history_years",
                      "num_credit_lines", "late_payments", "employment_years",
                      "loan_amount", "savings_ratio", "num_dependents"],
        "task_type": "classification",
        "class_balance": {"0_no_default": int(np.sum(y == 0)), "1_default": int(np.sum(y == 1))},
        "has_missing_values": True,
        "missing_rate": "~5%",
        "random_seed": 101,
    }
    return X, y, metadata


CREDIT_RISK_DESCRIPTION = """# Credit Risk Modeling

## Context

Predict whether a loan applicant will default within 12 months.
The dataset contains realistic messy data with missing values.

## Dataset

- **2000 loan applications**, 10 features:
  `age, income, debt_ratio, credit_history_years, num_credit_lines,
   late_payments, employment_years, loan_amount, savings_ratio, num_dependents`
- **~5% missing values** scattered across features
- Target: 0 = no default, 1 = default

## Task

Achieve **AUC-ROC >= 0.75** on the test set.

## Input Format

- `X_train`: Training features (1600, 10) - numpy array with NaN values
- `y_train`: Training labels (1600,) - binary 0/1
- `X_test`: Test features (400, 10) - numpy array with NaN values

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: AUC-ROC (higher is better)
- **Threshold**: >= 0.75

## Constraints

- Must handle NaN values (imputation required)
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 5: FRAUD DETECTION (MEDIUM — 1200)
# ============================================================================

def _load_fraud_detection_dataset():
    np.random.seed(202)
    n = 5000
    n_fraud = 150  # 3% fraud rate

    # Normal transactions
    n_normal = n - n_fraud
    amt_normal = np.random.lognormal(4.0, 1.2, n_normal)
    hour_normal = np.random.normal(14, 4, n_normal).clip(0, 23)
    dist_normal = np.random.exponential(15, n_normal)
    freq_normal = np.random.poisson(3, n_normal)
    merchant_risk = np.random.beta(2, 8, n_normal)
    card_present = np.random.binomial(1, 0.85, n_normal)
    velocity_1h = np.random.poisson(1, n_normal)
    country_risk = np.random.beta(1, 10, n_normal)

    # Fraudulent transactions (different distribution)
    amt_fraud = np.random.lognormal(6.0, 1.5, n_fraud)
    hour_fraud = np.random.choice([2, 3, 4, 22, 23], n_fraud) + np.random.normal(0, 0.5, n_fraud)
    dist_fraud = np.random.exponential(200, n_fraud)
    freq_fraud = np.random.poisson(8, n_fraud)
    merchant_risk_f = np.random.beta(5, 2, n_fraud)
    card_present_f = np.random.binomial(1, 0.15, n_fraud)
    velocity_1h_f = np.random.poisson(5, n_fraud)
    country_risk_f = np.random.beta(5, 3, n_fraud)

    X_normal = np.column_stack([amt_normal, hour_normal, dist_normal, freq_normal,
                                 merchant_risk, card_present, velocity_1h, country_risk])
    X_fraud = np.column_stack([amt_fraud, hour_fraud, dist_fraud, freq_fraud,
                                merchant_risk_f, card_present_f, velocity_1h_f, country_risk_f])

    X = np.vstack([X_normal, X_fraud])
    y = np.hstack([np.zeros(n_normal, dtype=int), np.ones(n_fraud, dtype=int)])

    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]

    metadata = {
        "dataset_name": "fraud_detection",
        "num_samples": n,
        "num_features": 8,
        "features": ["transaction_amount", "hour_of_day", "distance_from_home",
                      "transaction_frequency", "merchant_risk_score", "card_present",
                      "velocity_1h", "country_risk_score"],
        "task_type": "classification",
        "class_balance": {"0_legitimate": n_normal, "1_fraud": n_fraud},
        "imbalance_ratio": f"{n_normal}:{n_fraud} ({n_fraud/n*100:.1f}% fraud)",
        "random_seed": 202,
    }
    return X, y, metadata


FRAUD_DETECTION_DESCRIPTION = """# Fraud Detection

## Context

Classify transactions as legitimate or fraudulent.
The dataset has extreme class imbalance (~3% fraud rate).

## Dataset

- **5000 transactions**, 8 features:
  `transaction_amount, hour_of_day, distance_from_home, transaction_frequency,
   merchant_risk_score, card_present, velocity_1h, country_risk_score`
- **3% fraud rate** — extreme class imbalance

## Task

Achieve **F1 >= 0.50** on the test set.

## Input Format

- `X_train`: Training features (4000, 8) - numpy array
- `y_train`: Training labels (4000,) - binary 0/1, ~97% zeros
- `X_test`: Test features (1000, 8) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: F1 Score (higher is better)
- **Threshold**: >= 0.50

## Constraints

- Handle extreme imbalance (97:3)
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 6: CUSTOMER CHURN (MEDIUM — 1200)
# ============================================================================

def _load_customer_churn_dataset():
    np.random.seed(303)
    n = 3000

    tenure_months = np.random.exponential(24, n).clip(1, 72).astype(int)
    monthly_charges = np.random.normal(65, 30, n).clip(10, 200)
    total_charges = tenure_months * monthly_charges * (1 + np.random.normal(0, 0.1, n))
    num_products = np.random.poisson(2, n).clip(1, 6)
    support_calls = np.random.poisson(2, n)
    contract_type = np.random.choice([0, 1, 2], n, p=[0.5, 0.3, 0.2])  # month, year, 2-year
    payment_delay_days = np.random.exponential(3, n).clip(0, 60)
    has_online_backup = np.random.binomial(1, 0.4, n)
    has_tech_support = np.random.binomial(1, 0.35, n)

    # Feature engineering target: interactions matter
    churn_score = (
        -0.04 * tenure_months + 0.01 * monthly_charges
        + 0.15 * support_calls - 0.3 * contract_type
        + 0.02 * payment_delay_days - 0.2 * has_online_backup
        - 0.25 * has_tech_support - 0.1 * num_products
        + 0.005 * monthly_charges * (support_calls > 3).astype(float)
        + np.random.normal(0, 0.8, n)
    )
    prob = 1 / (1 + np.exp(-churn_score))
    y = (prob > 0.5).astype(int)

    X = np.column_stack([tenure_months, monthly_charges, total_charges, num_products,
                          support_calls, contract_type, payment_delay_days,
                          has_online_backup, has_tech_support])

    metadata = {
        "dataset_name": "customer_churn",
        "num_samples": n,
        "num_features": 9,
        "features": ["tenure_months", "monthly_charges", "total_charges", "num_products",
                      "support_calls", "contract_type", "payment_delay_days",
                      "has_online_backup", "has_tech_support"],
        "task_type": "classification",
        "class_balance": {"0_retained": int(np.sum(y == 0)), "1_churned": int(np.sum(y == 1))},
        "random_seed": 303,
    }
    return X, y, metadata


CUSTOMER_CHURN_DESCRIPTION = """# Customer Churn Prediction

## Context

Identify customers likely to leave a telecom company.
Feature interactions are important for prediction.

## Dataset

- **3000 customers**, 9 features:
  `tenure_months, monthly_charges, total_charges, num_products, support_calls,
   contract_type, payment_delay_days, has_online_backup, has_tech_support`
- Churn depends on feature interactions

## Task

Achieve **F1 >= 0.62** on the test set.

## Input Format

- `X_train`: Training features (2400, 9) - numpy array
- `y_train`: Training labels (2400,) - binary 0/1
- `X_test`: Test features (600, 9) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: F1 Score (higher is better)
- **Threshold**: >= 0.62

## Constraints

- Consider feature engineering
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 7: LOAN DEFAULT PROBABILITY (MEDIUM — 1200)
# ============================================================================

def _load_loan_default_dataset():
    np.random.seed(404)
    n = 2500

    loan_amount = np.random.lognormal(10, 0.8, n)
    interest_rate = np.random.normal(8, 3, n).clip(2, 25)
    annual_income = np.random.lognormal(11, 0.7, n)
    dti = (loan_amount * interest_rate / 100) / (annual_income / 12)
    dti = dti.clip(0, 2)
    fico_score = np.random.normal(700, 60, n).clip(300, 850).astype(int)
    employment_length = np.random.exponential(5, n).clip(0, 30)
    home_ownership = np.random.choice([0, 1, 2], n, p=[0.4, 0.45, 0.15])  # rent, mortgage, own
    purpose = np.random.choice([0, 1, 2, 3], n, p=[0.35, 0.25, 0.25, 0.15])
    open_accounts = np.random.poisson(8, n)
    delinquencies = np.random.poisson(0.5, n)
    inquiries_6mo = np.random.poisson(1, n)

    risk = (
        -0.005 * fico_score + 0.5 * dti + 0.00001 * loan_amount
        + 0.05 * interest_rate + 0.3 * delinquencies
        + 0.1 * inquiries_6mo - 0.03 * employment_length
        + np.random.normal(0, 0.6, n)
    )
    y = (1 / (1 + np.exp(-risk)) > 0.45).astype(int)

    X = np.column_stack([loan_amount, interest_rate, annual_income, dti, fico_score,
                          employment_length, home_ownership, purpose, open_accounts,
                          delinquencies, inquiries_6mo])

    metadata = {
        "dataset_name": "loan_default",
        "num_samples": n,
        "num_features": 11,
        "features": ["loan_amount", "interest_rate", "annual_income", "dti", "fico_score",
                      "employment_length", "home_ownership", "purpose", "open_accounts",
                      "delinquencies", "inquiries_6mo"],
        "task_type": "classification",
        "class_balance": {"0_repaid": int(np.sum(y == 0)), "1_defaulted": int(np.sum(y == 1))},
        "random_seed": 404,
    }
    return X, y, metadata


LOAN_DEFAULT_DESCRIPTION = """# Loan Default Prediction

## Context

Predict which borrowers will default on peer-to-peer loans.
FICO score and financial ratios are key predictors.

## Dataset

- **2500 loans**, 11 features:
  `loan_amount, interest_rate, annual_income, dti, fico_score,
   employment_length, home_ownership, purpose, open_accounts,
   delinquencies, inquiries_6mo`
- DTI (debt-to-income) is derived from other features

## Task

Achieve **AUC-ROC >= 0.72** on the test set.

## Input Format

- `X_train`: Training features (2000, 11) - numpy array
- `y_train`: Training labels (2000,) - binary 0/1
- `X_test`: Test features (500, 11) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: AUC-ROC (higher is better)
- **Threshold**: >= 0.72

## Constraints

- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 8: TIME SERIES FORECASTING (HARD — 1600)
# ============================================================================

def _load_timeseries_forecasting_dataset():
    np.random.seed(505)
    n_days = 730  # 2 years of daily data

    t = np.arange(n_days)
    trend = 0.05 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 365) + 5 * np.sin(2 * np.pi * t / 7)
    noise = np.random.normal(0, 3, n_days)
    y_raw = 100 + trend + seasonal + noise

    # Create lag features (supervised learning format)
    window = 14
    X_list = []
    y_list = []
    for i in range(window, n_days):
        features = []
        for lag in range(1, window + 1):
            features.append(y_raw[i - lag])
        # Rolling stats
        features.append(np.mean(y_raw[i - 7:i]))
        features.append(np.std(y_raw[i - 7:i]))
        features.append(np.mean(y_raw[i - 14:i]))
        features.append(i % 7)  # day of week
        features.append(i % 365)  # day of year
        X_list.append(features)
        y_list.append(y_raw[i])

    X = np.array(X_list)
    y = np.array(y_list)

    metadata = {
        "dataset_name": "timeseries_forecasting",
        "num_samples": len(X),
        "num_features": X.shape[1],
        "features": [f"lag_{i}" for i in range(1, window + 1)] + [
            "rolling_mean_7", "rolling_std_7", "rolling_mean_14", "day_of_week", "day_of_year"
        ],
        "task_type": "regression",
        "random_seed": 505,
    }
    return X, y, metadata


TIMESERIES_DESCRIPTION = """# Time Series Forecasting

## Context

Demand forecasting using historical data with trend and seasonal patterns.
The data has been converted to a supervised learning format with lag features.

## Dataset

- **716 daily observations** in supervised learning format
- 14 lag features + rolling statistics + calendar features
- Target: next-day demand value

## Task

Achieve **MAE <= 8.0** on the test set.

## Input Format

- `X_train`: Training features (572, 19) - numpy array
- `y_train`: Training targets (572,) - continuous floats
- `X_test`: Test features (144, 19) - numpy array

## Output Format

Return predictions as a numpy array or list of continuous float values.

## Evaluation

- **Metric**: MAE (lower is better)
- **Threshold**: <= 8.0

## Constraints

- Temporal autocorrelation in features
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 9: HOUSE PRICE REGRESSION (MEDIUM — 1200)
# ============================================================================

def _load_house_price_dataset():
    np.random.seed(606)
    n = 1500

    sqft = np.random.normal(1800, 600, n).clip(500, 5000)
    bedrooms = np.random.poisson(3, n).clip(1, 7)
    bathrooms = (bedrooms * 0.6 + np.random.normal(0, 0.5, n)).clip(1, 5).round(1)
    lot_size = np.random.lognormal(8.5, 0.5, n)
    year_built = np.random.normal(1985, 20, n).clip(1920, 2024).astype(int)
    garage_size = np.random.choice([0, 1, 2, 3], n, p=[0.1, 0.3, 0.45, 0.15])
    quality_score = np.random.normal(6, 2, n).clip(1, 10)
    neighborhood = np.random.choice([0, 1, 2, 3, 4], n)
    has_pool = np.random.binomial(1, 0.2, n)
    distance_downtown = np.random.exponential(8, n)

    # Inject outliers (luxury mansions, distressed sales)
    outlier_idx = np.random.choice(n, 30, replace=False)

    price = (
        80 * sqft + 15000 * bedrooms + 20000 * bathrooms
        + 0.5 * lot_size + 500 * (year_built - 1950)
        + 25000 * garage_size + 10000 * quality_score
        - 5000 * neighborhood + 30000 * has_pool
        - 3000 * distance_downtown
        + np.random.normal(0, 25000, n)
    )
    price = price.clip(50000, 2000000)
    price[outlier_idx] *= np.random.uniform(1.5, 3.0, 30)

    X = np.column_stack([sqft, bedrooms, bathrooms, lot_size, year_built,
                          garage_size, quality_score, neighborhood, has_pool, distance_downtown])
    y = price

    metadata = {
        "dataset_name": "house_prices",
        "num_samples": n,
        "num_features": 10,
        "features": ["sqft", "bedrooms", "bathrooms", "lot_size", "year_built",
                      "garage_size", "quality_score", "neighborhood", "has_pool", "distance_downtown"],
        "task_type": "regression",
        "has_outliers": True,
        "random_seed": 606,
    }
    return X, y, metadata


HOUSE_PRICE_DESCRIPTION = """# House Price Regression

## Context

Predict property valuations based on house attributes.
The dataset contains outliers (luxury homes, distressed sales).

## Dataset

- **1500 properties**, 10 features:
  `sqft, bedrooms, bathrooms, lot_size, year_built, garage_size,
   quality_score, neighborhood, has_pool, distance_downtown`
- Contains outliers (~30 extreme prices)
- Features on different scales

## Task

Achieve **RMSE <= 80000** on the test set.

## Input Format

- `X_train`: Training features (1200, 10) - numpy array
- `y_train`: Training targets (1200,) - price values
- `X_test`: Test features (300, 10) - numpy array

## Output Format

Return predictions as a numpy array or list of continuous float values (prices).

## Evaluation

- **Metric**: RMSE (lower is better)
- **Threshold**: <= 80000

## Constraints

- Handle outliers appropriately
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 10: SENTIMENT ANALYSIS (HARD — 1600)
# ============================================================================

def _load_sentiment_dataset():
    np.random.seed(707)
    n = 2000

    # Simulate TF-IDF features for a text classification task
    n_features = 50
    X_pos = np.random.exponential(0.3, (n // 2, n_features))
    X_neg = np.random.exponential(0.3, (n // 2, n_features))

    # Positive sentiment signal in features 0-15
    X_pos[:, :15] += np.random.exponential(0.5, (n // 2, 15))
    # Negative sentiment signal in features 20-35
    X_neg[:, 20:35] += np.random.exponential(0.5, (n // 2, 15))

    # Shared noise features
    X_pos[:, 40:] = np.random.normal(0.5, 0.3, (n // 2, 10))
    X_neg[:, 40:] = np.random.normal(0.5, 0.3, (n // 2, 10))

    X = np.vstack([X_pos, X_neg])
    y = np.hstack([np.ones(n // 2, dtype=int), np.zeros(n // 2, dtype=int)])

    idx = np.random.permutation(n)
    X, y = X[idx], y[idx]

    metadata = {
        "dataset_name": "sentiment_analysis",
        "num_samples": n,
        "num_features": n_features,
        "features": [f"tfidf_{i}" for i in range(n_features)],
        "task_type": "classification",
        "class_balance": {"0_negative": int(np.sum(y == 0)), "1_positive": int(np.sum(y == 1))},
        "random_seed": 707,
    }
    return X, y, metadata


SENTIMENT_DESCRIPTION = """# Sentiment Analysis

## Context

Classify product reviews as positive or negative based on TF-IDF features.
Each review is represented as a 50-dimensional feature vector.

## Dataset

- **2000 reviews**, 50 TF-IDF features
- Balanced classes (50/50)
- Signal concentrated in different feature ranges
- Some features are noise

## Task

Achieve **Accuracy >= 0.82** on the test set.

## Input Format

- `X_train`: Training features (1600, 50) - TF-IDF vectors
- `y_train`: Training labels (1600,) - binary 0/1
- `X_test`: Test features (400, 50) - TF-IDF vectors

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.82

## Constraints

- High dimensionality relative to signal
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 11: MULTI-CLASS CLASSIFICATION (HARD — 1600)
# ============================================================================

def _load_multiclass_dataset():
    np.random.seed(808)
    n_per_class = 300
    n_classes = 5
    n_features = 12

    X_parts = []
    y_parts = []
    for c in range(n_classes):
        center = np.zeros(n_features)
        center[c * 2:(c + 1) * 2] = 3.0
        center += np.random.normal(0, 0.3, n_features)
        X_c = np.random.normal(center, 1.2, (n_per_class, n_features))
        y_c = np.full(n_per_class, c, dtype=int)
        X_parts.append(X_c)
        y_parts.append(y_c)

    X = np.vstack(X_parts)
    y = np.hstack(y_parts)
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]

    metadata = {
        "dataset_name": "multiclass_classification",
        "num_samples": len(X),
        "num_features": n_features,
        "features": [f"feature_{i}" for i in range(n_features)],
        "task_type": "classification",
        "num_classes": n_classes,
        "random_seed": 808,
    }
    return X, y, metadata


MULTICLASS_DESCRIPTION = """# Multi-Class Classification

## Context

Classify products into 5 defect categories based on sensor measurements.
Each category requires different remediation.

## Dataset

- **1500 products**, 12 sensor features, 5 defect classes (0-4)
- Each class has signal concentrated in different feature pairs
- Balanced classes (300 per class)

## Task

Achieve **Macro F1 >= 0.70** on the test set.

## Input Format

- `X_train`: Training features (1200, 12) - numpy array
- `y_train`: Training labels (1200,) - integers 0-4
- `X_test`: Test features (300, 12) - numpy array

## Output Format

Return predictions as a numpy array or list of integers (0-4).

## Evaluation

- **Metric**: Macro F1 (higher is better)
- **Threshold**: >= 0.70

## Constraints

- Multi-class problem (5 classes)
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 12: FEATURE SELECTION CHALLENGE (HARD — 1600)
# ============================================================================

def _load_feature_selection_dataset():
    np.random.seed(909)
    n = 1000
    n_informative = 5
    n_noise = 45
    n_total = n_informative + n_noise

    # Informative features
    X_info = np.random.normal(0, 1, (n, n_informative))
    y = (X_info[:, 0] * 2 + X_info[:, 1] * 1.5 - X_info[:, 2] + 0.5 * X_info[:, 3]
         + 0.3 * X_info[:, 4] + np.random.normal(0, 0.3, n))
    y = (y > np.median(y)).astype(int)

    # Noise features (pure random, uncorrelated with target)
    X_noise = np.random.normal(0, 1, (n, n_noise))

    # Duplicate features (correlated with informative)
    X_dup1 = X_info[:, 0:1] + np.random.normal(0, 0.1, (n, 1))
    X_dup2 = X_info[:, 1:2] * 2 + np.random.normal(0, 0.2, (n, 1))

    X = np.hstack([X_info, X_noise, X_dup1, X_dup2])

    # Shuffle column order
    col_perm = np.random.permutation(X.shape[1])
    X = X[:, col_perm]

    metadata = {
        "dataset_name": "feature_selection",
        "num_samples": n,
        "num_features": X.shape[1],
        "features": [f"feature_{i}" for i in range(X.shape[1])],
        "task_type": "classification",
        "n_informative": n_informative,
        "n_noise": n_noise,
        "n_duplicate": 2,
        "random_seed": 909,
    }
    return X, y, metadata


FEATURE_SELECTION_DESCRIPTION = """# Feature Selection Challenge

## Context

Build a classifier from a dataset with many noise features.
Only ~5 features are actually predictive; the rest are noise or duplicates.

## Dataset

- **1000 patients**, 52 features
- Only **5 features are informative**
- 45 features are pure noise
- 2 features are near-duplicates of informative features
- Columns are shuffled

## Task

Achieve **Accuracy >= 0.85** on the test set.

## Input Format

- `X_train`: Training features (800, 52) - numpy array
- `y_train`: Training labels (800,) - binary 0/1
- `X_test`: Test features (200, 52) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.85

## Constraints

- Handle high noise-to-signal ratio
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 13: MODEL EXPLAINABILITY (EXPERT — 2000)
# ============================================================================

def _load_explainability_dataset():
    np.random.seed(111)
    n = 800

    # Clear, interpretable features with known effects
    credit_util = np.random.beta(2, 5, n)  # 0-1 ratio
    payment_history = np.random.normal(0.85, 0.15, n).clip(0, 1)
    income_log = np.random.normal(11, 0.5, n)
    age = np.random.normal(40, 12, n).clip(21, 70)
    num_accounts = np.random.poisson(5, n)

    # Known ground truth: approval = f(credit_util, payment_history, income)
    score = (-3.0 * credit_util + 2.5 * payment_history + 0.5 * (income_log - 10)
             + 0.01 * age - 0.1 * num_accounts + np.random.normal(0, 0.3, n))
    y = (score > 0).astype(int)

    X = np.column_stack([credit_util, payment_history, income_log, age, num_accounts])

    metadata = {
        "dataset_name": "model_explainability",
        "num_samples": n,
        "num_features": 5,
        "features": ["credit_utilization", "payment_history", "income_log", "age", "num_accounts"],
        "task_type": "classification",
        "ground_truth_importance": {
            "credit_utilization": "high_negative",
            "payment_history": "high_positive",
            "income_log": "medium_positive",
            "age": "low_positive",
            "num_accounts": "low_negative",
        },
        "random_seed": 111,
    }
    return X, y, metadata


EXPLAINABILITY_DESCRIPTION = """# Model Explainability Challenge

## Context

Build an interpretable loan approval model where feature importance
must align with domain knowledge.

## Dataset

- **800 applicants**, 5 features:
  `credit_utilization, payment_history, income_log, age, num_accounts`
- Ground truth: certain features have known positive/negative effects

## Task

Achieve **Accuracy >= 0.82** on the test set.

## Input Format

- `X_train`: Training features (640, 5) - numpy array
- `y_train`: Training labels (640,) - binary 0/1
- `X_test`: Test features (160, 5) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.82

## Constraints

- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 14: HYPERPARAMETER OPTIMIZATION (EXPERT — 2000)
# ============================================================================

def _load_hyperparameter_dataset():
    np.random.seed(222)
    n = 1200
    n_features = 20

    # Non-linear dataset that rewards careful hyperparameter tuning
    from sklearn.datasets import make_classification
    X, y = make_classification(
        n_samples=n, n_features=n_features, n_informative=10,
        n_redundant=5, n_clusters_per_class=3, flip_y=0.08,
        class_sep=0.8, random_state=222
    )

    metadata = {
        "dataset_name": "hyperparameter_optimization",
        "num_samples": n,
        "num_features": n_features,
        "task_type": "classification",
        "random_seed": 222,
    }
    return X, y, metadata


HYPERPARAMETER_DESCRIPTION = """# Hyperparameter Optimization Challenge

## Context

A dataset designed so that default sklearn parameters produce mediocre results.
Systematic hyperparameter tuning is required to reach the threshold.

## Dataset

- **1200 samples**, 20 features
- 10 informative, 5 redundant, 5 noise
- 3 clusters per class with 8% label noise
- Low class separation

## Task

Achieve **Accuracy >= 0.84** on the test set.

## Input Format

- `X_train`: Training features (960, 20) - numpy array
- `y_train`: Training labels (960,) - binary 0/1
- `X_test`: Test features (240, 20) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.84

## Constraints

- Systematic tuning required
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 15: PRODUCTION INFERENCE CONSTRAINT (EXPERT — 2000)
# ============================================================================

def _load_production_inference_dataset():
    np.random.seed(333)
    n = 5000
    n_features = 30

    from sklearn.datasets import make_classification
    X, y = make_classification(
        n_samples=n, n_features=n_features, n_informative=15,
        n_redundant=10, flip_y=0.05, random_state=333
    )

    metadata = {
        "dataset_name": "production_inference",
        "num_samples": n,
        "num_features": n_features,
        "task_type": "classification",
        "random_seed": 333,
    }
    return X, y, metadata


PRODUCTION_INFERENCE_DESCRIPTION = """# Production Inference Constraint

## Context

Build a model with a strict latency budget.
Heavy ensemble methods will timeout — balance accuracy vs. speed.

## Dataset

- **5000 samples**, 30 features
- 15 informative, 10 redundant, 5 noise

## Task

Achieve **Accuracy >= 0.88** on the test set within the latency constraint.

## Input Format

- `X_train`: Training features (4000, 30) - numpy array
- `y_train`: Training labels (4000,) - binary 0/1
- `X_test`: Test features (1000, 30) - numpy array

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.88
- **Latency constraint**: <= 200ms total execution

## Constraints

- Maximum latency: 200ms for entire train_and_predict execution
- All imports must be inside the function body
"""


# ============================================================================
# PROBLEM 16: DRIFT DETECTION SIMULATION (EXPERT — 2000)
# ============================================================================

def _load_drift_detection_dataset():
    np.random.seed(444)

    # Training data: distribution D1
    n_train_total = 1500
    X_train_d1 = np.random.normal([2, 3, 1, 0, -1, 2, 0, 1], 1.0, (n_train_total, 8))
    y_train_score = (X_train_d1[:, 0] * 1.5 + X_train_d1[:, 1] * 0.8
                     - X_train_d1[:, 2] * 1.2 + np.random.normal(0, 0.5, n_train_total))
    y_train_all = (y_train_score > np.median(y_train_score)).astype(int)

    # Test data: distribution D2 (shifted — simulates concept drift)
    n_test_total = 500
    X_test_d2 = np.random.normal([3, 2, 2, 1, -2, 1, 1, 0], 1.3, (n_test_total, 8))
    y_test_score = (X_test_d2[:, 0] * 1.5 + X_test_d2[:, 1] * 0.8
                    - X_test_d2[:, 2] * 1.2 + np.random.normal(0, 0.5, n_test_total))
    y_test_all = (y_test_score > np.median(y_test_score)).astype(int)

    X = np.vstack([X_train_d1, X_test_d2])
    y = np.hstack([y_train_all, y_test_all])

    metadata = {
        "dataset_name": "drift_detection",
        "num_samples": len(X),
        "num_features": 8,
        "features": [f"sensor_{i}" for i in range(8)],
        "task_type": "classification",
        "drift_type": "covariate_shift",
        "train_distribution": "D1 (mean=[2,3,1,0,-1,2,0,1], std=1.0)",
        "test_distribution": "D2 (mean=[3,2,2,1,-2,1,1,0], std=1.3)",
        "random_seed": 444,
    }
    return X, y, metadata


DRIFT_DETECTION_DESCRIPTION = """# Drift Detection Simulation

## Context

Train on historical data, but test on data with shifted distributions (concept drift).
The sensor readings have changed between training and test periods.

## Dataset

- **2000 samples**, 8 sensor features
- Training data follows distribution D1
- Test data follows distribution D2 (shifted means and variance)
- Covariate shift scenario

## Task

Achieve **Accuracy >= 0.68** on the test set despite distribution drift.

## Input Format

- `X_train`: Training features (1200, 8) from distribution D1
- `y_train`: Training labels (1200,) - binary 0/1
- `X_test`: Test features (300, 8) from distribution D2

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.68

## Constraints

- Handle distribution shift
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 17: RECOMMENDER SYSTEM (HARD — 1600)
# ============================================================================

def _load_recommender_dataset():
    np.random.seed(555)
    n_users = 200
    n_items = 50
    n_interactions = 4000

    # User features
    user_age = np.random.normal(30, 10, n_users).clip(16, 65)
    user_activity = np.random.exponential(5, n_users)

    # Item features
    item_popularity = np.random.exponential(3, n_items)
    item_category = np.random.choice(5, n_items)

    # Generate interactions
    user_ids = np.random.choice(n_users, n_interactions)
    item_ids = np.random.choice(n_items, n_interactions)

    # Rating = user_affinity_to_category + item_quality + noise
    ratings = []
    features = []
    for u, i in zip(user_ids, item_ids):
        # User-item interaction features
        f = [
            user_age[u], user_activity[u],
            item_popularity[i], float(item_category[i]),
            user_age[u] * item_popularity[i] / 100,
            float(item_category[i] == int(user_age[u]) % 5),
        ]
        rating = (
            3.0 + 0.5 * np.log1p(item_popularity[i])
            + 0.3 * (item_category[i] == int(user_age[u]) % 5)
            - 0.01 * abs(user_age[u] - 30)
            + 0.1 * user_activity[u]
            + np.random.normal(0, 0.8)
        )
        rating = np.clip(rating, 1, 5)
        features.append(f)
        ratings.append(rating)

    X = np.array(features)
    y = np.array(ratings)

    metadata = {
        "dataset_name": "recommender_system",
        "num_samples": n_interactions,
        "num_features": 6,
        "features": ["user_age", "user_activity", "item_popularity",
                      "item_category", "age_popularity_interaction", "category_match"],
        "task_type": "regression",
        "rating_range": "1.0 to 5.0",
        "random_seed": 555,
    }
    return X, y, metadata


RECOMMENDER_DESCRIPTION = """# Recommender System

## Context

Predict user ratings for items based on user-item interaction features.
Pure collaborative filtering is not possible — use the provided features.

## Dataset

- **4000 user-item interactions**, 6 features:
  `user_age, user_activity, item_popularity, item_category,
   age_popularity_interaction, category_match`
- Target: rating (1.0 to 5.0, continuous)
- Interaction features are pre-computed

## Task

Achieve **MAE <= 0.65** on the test set.

## Input Format

- `X_train`: Training features (3200, 6) - numpy array
- `y_train`: Training targets (3200,) - ratings 1.0 to 5.0
- `X_test`: Test features (800, 6) - numpy array

## Output Format

Return predictions as a numpy array or list of continuous float values (1.0-5.0).

## Evaluation

- **Metric**: MAE (lower is better)
- **Threshold**: <= 0.65

## Constraints

- No user/item IDs available
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# PROBLEM 18: PIPELINE OPTIMIZATION (EXPERT — 2000)
# ============================================================================

def _load_pipeline_optimization_dataset():
    np.random.seed(666)
    n = 2000
    n_features = 25

    # Mix of feature types
    X_numeric = np.random.normal(0, 1, (n, 10))
    X_skewed = np.random.exponential(2, (n, 5))
    X_binary = np.random.binomial(1, 0.3, (n, 5))
    X_ordinal = np.random.choice([1, 2, 3, 4, 5], (n, 5))

    X = np.hstack([X_numeric, X_skewed, X_binary, X_ordinal])

    # Inject missing values (10% random)
    missing = np.random.random(X.shape) < 0.10
    X = X.astype(float)
    X[missing] = np.nan

    # Non-linear target with interactions
    y_score = (
        X_numeric[:, 0] * 2 + np.sin(X_numeric[:, 1]) * 3
        + X_skewed[:, 0] * 0.5 - X_binary[:, 2] * 1.5
        + X_ordinal[:, 0] * 0.3
        + X_numeric[:, 0] * X_skewed[:, 1] * 0.2
        + np.random.normal(0, 0.5, n)
    )
    y = (y_score > np.median(y_score)).astype(int)

    metadata = {
        "dataset_name": "pipeline_optimization",
        "num_samples": n,
        "num_features": n_features,
        "features": ([f"numeric_{i}" for i in range(10)]
                     + [f"skewed_{i}" for i in range(5)]
                     + [f"binary_{i}" for i in range(5)]
                     + [f"ordinal_{i}" for i in range(5)]),
        "task_type": "classification",
        "has_missing_values": True,
        "missing_rate": "~10%",
        "feature_types": {"numeric": 10, "skewed": 5, "binary": 5, "ordinal": 5},
        "random_seed": 666,
    }
    return X, y, metadata


PIPELINE_DESCRIPTION = """# Pipeline Optimization Challenge

## Context

A messy production dataset with multiple feature types and missing values.
Build a complete preprocessing and modeling pipeline.

## Dataset

- **2000 samples**, 25 features:
  - 10 numeric (Gaussian)
  - 5 skewed (exponential distribution)
  - 5 binary (0/1)
  - 5 ordinal (1-5 scale)
- **~10% missing values** randomly scattered

## Task

Achieve **Accuracy >= 0.78** on the test set.

## Input Format

- `X_train`: Training features (1600, 25) - numpy array with NaN values
- `y_train`: Training labels (1600,) - binary 0/1
- `X_test`: Test features (400, 25) - numpy array with NaN values

## Output Format

Return predictions as a numpy array or list of binary values (0 or 1).

## Evaluation

- **Metric**: Accuracy (higher is better)
- **Threshold**: >= 0.78

## Constraints

- Must handle missing values
- Multiple feature types require different preprocessing
- All imports must be inside the function body
- Timeout: 5 seconds
"""


# ============================================================================
# CENTRAL REGISTRY
# ============================================================================

PROBLEM_REGISTRY = {
    # ==================== EASY (800) ====================
    "linear-binary-classification": ProblemDefinition(
        slug="linear-binary-classification",
        title="Linear Binary Classification",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.80,
        dataset_loader=_load_linear_binary_dataset,
        description=LINEAR_BINARY_DESCRIPTION,
        difficulty="easy",
        difficulty_rating=800,
        category="fundamentals",
    ),
    "regression-fundamentals": ProblemDefinition(
        slug="regression-fundamentals",
        title="Regression Fundamentals",
        task_type="regression",
        default_metric="rmse",
        allowed_metrics=["rmse"],
        submission_threshold=20.0,
        dataset_loader=_load_regression_fundamentals_dataset,
        description=REGRESSION_FUNDAMENTALS_DESCRIPTION,
        difficulty="easy",
        difficulty_rating=800,
        category="fundamentals",
    ),
    "imbalanced-f1-classification": ProblemDefinition(
        slug="imbalanced-f1-classification",
        title="Imbalanced Classification (F1 Score)",
        task_type="classification",
        default_metric="f1",
        allowed_metrics=["f1"],
        submission_threshold=0.60,
        dataset_loader=_load_imbalanced_classification_dataset,
        description=IMBALANCED_CLASSIFICATION_DESCRIPTION,
        difficulty="easy",
        difficulty_rating=800,
        category="fundamentals",
    ),

    # ==================== MEDIUM (1200) ====================
    "credit-risk-modeling": ProblemDefinition(
        slug="credit-risk-modeling",
        title="Credit Risk Modeling",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy", "f1"],
        submission_threshold=0.75,
        dataset_loader=_load_credit_risk_dataset,
        description=CREDIT_RISK_DESCRIPTION,
        difficulty="medium",
        difficulty_rating=1200,
        category="finance",
    ),
    "fraud-detection": ProblemDefinition(
        slug="fraud-detection",
        title="Fraud Detection",
        task_type="classification",
        default_metric="f1",
        allowed_metrics=["f1"],
        submission_threshold=0.50,
        dataset_loader=_load_fraud_detection_dataset,
        description=FRAUD_DETECTION_DESCRIPTION,
        difficulty="medium",
        difficulty_rating=1200,
        category="finance",
    ),
    "customer-churn": ProblemDefinition(
        slug="customer-churn",
        title="Customer Churn Prediction",
        task_type="classification",
        default_metric="f1",
        allowed_metrics=["f1"],
        submission_threshold=0.62,
        dataset_loader=_load_customer_churn_dataset,
        description=CUSTOMER_CHURN_DESCRIPTION,
        difficulty="medium",
        difficulty_rating=1200,
        category="business",
    ),
    "loan-default": ProblemDefinition(
        slug="loan-default",
        title="Loan Default Prediction",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy", "f1"],
        submission_threshold=0.72,
        dataset_loader=_load_loan_default_dataset,
        description=LOAN_DEFAULT_DESCRIPTION,
        difficulty="medium",
        difficulty_rating=1200,
        category="finance",
    ),
    "house-price-regression": ProblemDefinition(
        slug="house-price-regression",
        title="House Price Regression",
        task_type="regression",
        default_metric="rmse",
        allowed_metrics=["rmse", "mae"],
        submission_threshold=80000.0,
        dataset_loader=_load_house_price_dataset,
        description=HOUSE_PRICE_DESCRIPTION,
        difficulty="medium",
        difficulty_rating=1200,
        category="real_estate",
    ),

    # ==================== HARD (1600) ====================
    "timeseries-forecasting": ProblemDefinition(
        slug="timeseries-forecasting",
        title="Time Series Forecasting",
        task_type="regression",
        default_metric="mae",
        allowed_metrics=["mae"],
        submission_threshold=8.0,
        dataset_loader=_load_timeseries_forecasting_dataset,
        description=TIMESERIES_DESCRIPTION,
        difficulty="hard",
        difficulty_rating=1600,
        category="forecasting",
    ),
    "sentiment-analysis": ProblemDefinition(
        slug="sentiment-analysis",
        title="Sentiment Analysis",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy", "f1"],
        submission_threshold=0.82,
        dataset_loader=_load_sentiment_dataset,
        description=SENTIMENT_DESCRIPTION,
        difficulty="hard",
        difficulty_rating=1600,
        category="nlp",
    ),
    "multiclass-classification": ProblemDefinition(
        slug="multiclass-classification",
        title="Multi-Class Classification",
        task_type="classification",
        default_metric="f1",
        allowed_metrics=["f1"],
        submission_threshold=0.70,
        dataset_loader=_load_multiclass_dataset,
        description=MULTICLASS_DESCRIPTION,
        difficulty="hard",
        difficulty_rating=1600,
        category="manufacturing",
    ),
    "feature-selection": ProblemDefinition(
        slug="feature-selection",
        title="Feature Selection Challenge",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.85,
        dataset_loader=_load_feature_selection_dataset,
        description=FEATURE_SELECTION_DESCRIPTION,
        difficulty="hard",
        difficulty_rating=1600,
        category="biomedical",
    ),
    "recommender-system": ProblemDefinition(
        slug="recommender-system",
        title="Recommender System",
        task_type="regression",
        default_metric="mae",
        allowed_metrics=["mae"],
        submission_threshold=0.65,
        dataset_loader=_load_recommender_dataset,
        description=RECOMMENDER_DESCRIPTION,
        difficulty="hard",
        difficulty_rating=1600,
        category="recommendations",
    ),

    # ==================== EXPERT (2000) ====================
    "model-explainability": ProblemDefinition(
        slug="model-explainability",
        title="Model Explainability Challenge",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.82,
        dataset_loader=_load_explainability_dataset,
        description=EXPLAINABILITY_DESCRIPTION,
        difficulty="expert",
        difficulty_rating=2000,
        category="mlops",
    ),
    "hyperparameter-optimization": ProblemDefinition(
        slug="hyperparameter-optimization",
        title="Hyperparameter Optimization Challenge",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.84,
        dataset_loader=_load_hyperparameter_dataset,
        description=HYPERPARAMETER_DESCRIPTION,
        difficulty="expert",
        difficulty_rating=2000,
        category="optimization",
    ),
    "production-inference": ProblemDefinition(
        slug="production-inference",
        title="Production Inference Constraint",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.88,
        dataset_loader=_load_production_inference_dataset,
        description=PRODUCTION_INFERENCE_DESCRIPTION,
        difficulty="expert",
        difficulty_rating=2000,
        category="production",
        constraints={"max_latency_ms": 200},
    ),
    "drift-detection": ProblemDefinition(
        slug="drift-detection",
        title="Drift Detection Simulation",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.68,
        dataset_loader=_load_drift_detection_dataset,
        description=DRIFT_DETECTION_DESCRIPTION,
        difficulty="expert",
        difficulty_rating=2000,
        category="mlops",
        hidden_test_ratio=0.25,
    ),
    "pipeline-optimization": ProblemDefinition(
        slug="pipeline-optimization",
        title="Pipeline Optimization Challenge",
        task_type="classification",
        default_metric="accuracy",
        allowed_metrics=["accuracy"],
        submission_threshold=0.78,
        dataset_loader=_load_pipeline_optimization_dataset,
        description=PIPELINE_DESCRIPTION,
        difficulty="expert",
        difficulty_rating=2000,
        category="engineering",
    ),
}


def get_problem_definition(slug: str) -> ProblemDefinition:
    """
    Get problem definition by slug.

    Raises:
        ValueError: If problem slug not found
    """
    if slug not in PROBLEM_REGISTRY:
        raise ValueError(f"Problem '{slug}' not found. Available: {list(PROBLEM_REGISTRY.keys())}")
    return PROBLEM_REGISTRY[slug]


def list_problems():
    """Return list of all problem definitions."""
    return list(PROBLEM_REGISTRY.values())


def list_problems_by_difficulty(difficulty: str = None):
    """Return problems filtered by difficulty."""
    if difficulty is None:
        return list_problems()
    return [p for p in PROBLEM_REGISTRY.values() if p.difficulty == difficulty]


def list_problems_by_category(category: str):
    """Return problems filtered by category."""
    return [p for p in PROBLEM_REGISTRY.values() if p.category == category]
