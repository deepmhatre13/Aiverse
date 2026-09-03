"""All 40 production-grade ML problems for load_problems command."""

PROBLEMS = [
    # ==================== EASY (800) — 8 problems ====================
    {
        "slug": "linear-binary-classification",
        "title": "Linear Binary Classification",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "classification",
        "metric": "ACCURACY",
        "points": 800,
        "description": """You are given a tabular dataset with 2 features (X1, X2) and a binary label (0 or 1).
The classes are linearly separable. Train a classifier that achieves >= 0.92 accuracy on the held-out test set.
Constraints: scikit-learn only, random_state=42, training under 10 seconds.""",
        "starter_code": """import numpy as np
from sklearn.linear_model import LogisticRegression

def solve(X_train, y_train, X_test):
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)
    return model.predict(X_test)
""",
        "tags": ["classification", "logistic_regression", "sklearn"],
        "hints": [
            "Linear classifiers work well when classes are linearly separable",
            "Try LogisticRegression, LinearSVC, or SGDClassifier",
            "StandardScaler often improves convergence speed",
        ],
    },
    {
        "slug": "regression-fundamentals",
        "title": "Regression Fundamentals",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "regression",
        "metric": "RMSE",
        "points": 800,
        "description": """A real-estate dataset with 5 numerical features. Predict continuous sale prices.
Achieve RMSE <= 12000 on the test set. Features: sqft_living, bedrooms, bathrooms, floors, yr_built.""",
        "starter_code": """import numpy as np
from sklearn.linear_model import LinearRegression

def solve(X_train, y_train, X_test):
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model.predict(X_test)
""",
        "hints": [
            "Feature scaling helps linear models converge faster",
            "Ridge regression adds regularization and often outperforms plain OLS",
            "Check for skewed target variable — log transform can help",
        ],
    },
    {
        "slug": "imbalanced-f1-classification",
        "title": "Imbalanced Classification",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "classification",
        "metric": "F1",
        "points": 800,
        "description": """Medical screening dataset: 95% negative, 5% positive. Achieve macro F1 >= 0.75.
Naive all-negative classifiers achieve 95% accuracy but F1 = 0.""",
        "hints": [
            "Use class_weight='balanced' in sklearn classifiers",
            "RandomForestClassifier with class_weight='balanced_subsample' is strong",
            "Try lowering the decision threshold from 0.5 to 0.3",
        ],
    },
    {
        "slug": "feature-scaling-pipeline",
        "title": "Feature Scaling Pipeline",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "feature_engineering",
        "metric": "ACCURACY",
        "points": 800,
        "description": """Build a Pipeline([('scaler', ...), ('model', ...)]) achieving >= 0.88 accuracy.
Features on wildly different scales: age, income, credit_score, num_transactions, years_employed.""",
        "hints": [
            "Use sklearn.pipeline.Pipeline with StandardScaler",
            "Distance-based models require scaling",
            "Fit scaler only on training data inside the pipeline",
        ],
    },
    {
        "slug": "cross-validation-correct",
        "title": "Cross-Validation Without Leakage",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "evaluation_metrics",
        "metric": "CV_SCORE",
        "points": 800,
        "description": """Implement 5-fold cross-validation CORRECTLY using a Pipeline.
Return mean_cv_score and std_cv_score. Target: mean_cv_score >= 0.85. No data leakage.""",
        "hints": [
            "Never fit scaler on all data before CV",
            "Use cross_val_score with a Pipeline object",
            "Scaling must happen inside each fold",
        ],
    },
    {
        "slug": "confusion-matrix-metrics",
        "title": "Confusion Matrix Metrics",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "evaluation_metrics",
        "metric": "EXACT_MATCH",
        "points": 800,
        "description": """Given a 3-class confusion matrix, compute precision, recall, F1 per class,
macro F1, weighted F1, and Cohen's Kappa. Implement from scratch (no sklearn.metrics).""",
        "hints": [
            "Precision = TP / (TP + FP) per class",
            "Recall = TP / (TP + FN) per class",
            "Cohen's Kappa accounts for chance agreement",
        ],
    },
    {
        "slug": "missing-data-imputation",
        "title": "Missing Data Imputation Strategy",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "feature_engineering",
        "metric": "RMSE",
        "points": 800,
        "description": """Housing dataset with MCAR, MAR, and MNAR missing values. Impute appropriately
and train a regressor to predict loan_amount. Achieve RMSE <= 8500.""",
        "hints": [
            "MCAR: mean/median imputation is acceptable",
            "MAR: use predictive imputation or KNN imputer",
            "MNAR: model the missingness mechanism",
        ],
    },
    {
        "slug": "polynomial-feature-interactions",
        "title": "Polynomial Feature Interactions",
        "difficulty": "easy",
        "category": "Fundamentals",
        "concept_tag": "feature_engineering",
        "metric": "R2",
        "points": 800,
        "description": """Non-linear relationship between features and target. Use PolynomialFeatures
to achieve R² >= 0.88. No tree-based models — linear models + feature engineering only.""",
        "hints": [
            "PolynomialFeatures(degree=2) captures interactions",
            "Include x1², x2*x3, log(x1) terms",
            "Linear regression with good features beats naive linear",
        ],
    },
    # ==================== MEDIUM (1200) — 11 problems ====================
    {
        "slug": "credit-risk-calibrated",
        "title": "Credit Risk with Probability Calibration",
        "difficulty": "medium",
        "category": "Finance",
        "concept_tag": "classification",
        "metric": "LOG_LOSS",
        "points": 1200,
        "description": """Predict probability of loan default. Use CalibratedClassifierCV.
Achieve log-loss <= 0.38. Handle categorical features correctly.""",
        "hints": [
            "Raw model probabilities are often poorly calibrated",
            "CalibratedClassifierCV with isotonic or sigmoid method",
            "OneHotEncoder for categorical features in a Pipeline",
        ],
    },
    {
        "slug": "fraud-detection",
        "title": "Real-Time Fraud Detection",
        "difficulty": "medium",
        "category": "Finance",
        "concept_tag": "classification",
        "metric": "F1",
        "points": 1200,
        "description": """Credit card fraud at 0.17% rate. Achieve F1 >= 0.82 on minority class.
1000 predictions must complete in under 100ms. Do NOT use amount in top 3 features.""",
        "hints": [
            "Extreme imbalance requires SMOTE or class weights",
            "LightGBM is fast for inference",
            "Amount correlates with fraud in training but not production",
        ],
    },
    {
        "slug": "customer-churn-interpretable",
        "title": "Customer Churn with Explainability",
        "difficulty": "medium",
        "category": "Business",
        "concept_tag": "ensemble_learning",
        "metric": "F1+SHAP",
        "points": 1200,
        "description": """Telecom churn: F1 >= 0.78 AND SHAP TreeExplainer with top 3 features matching
contract_type, tenure, monthly_charges. Return (y_pred, shap_values).""",
        "hints": [
            "Use tree-based model for SHAP TreeExplainer",
            "RandomForest or XGBoost with tuned hyperparameters",
            "Verify SHAP feature importance matches domain knowledge",
        ],
    },
    {
        "slug": "house-price-robust",
        "title": "House Price — Robust Regression",
        "difficulty": "medium",
        "category": "Real Estate",
        "concept_tag": "regression",
        "metric": "RMSE",
        "points": 1200,
        "description": """8% outliers injected in sqft, price, age columns. Detect and handle outliers
before training. Achieve RMSE <= 25000. Return (y_pred, outlier_indices).""",
        "hints": [
            "IQR method or Isolation Forest for outlier detection",
            "HuberRegressor is robust to outliers",
            "Remove or cap outliers before training",
        ],
    },
    {
        "slug": "multi-label-classification",
        "title": "Multi-Label Text Topic Classification",
        "difficulty": "medium",
        "category": "NLP",
        "concept_tag": "classification",
        "metric": "HAMMING_LOSS",
        "points": 1200,
        "description": """Tag news articles with multiple categories simultaneously.
Achieve Hamming Loss <= 0.12 using TF-IDF + OneVsRestClassifier or ClassifierChain.""",
        "hints": [
            "Multi-label is different from multi-class",
            "TfidfVectorizer for text features",
            "ClassifierChain captures label correlations",
        ],
    },
    {
        "slug": "timeseries-features",
        "title": "Time Series Feature Engineering",
        "difficulty": "medium",
        "category": "Forecasting",
        "concept_tag": "feature_engineering",
        "metric": "MAE",
        "points": 1200,
        "description": """Engineer lag, rolling, and calendar features for retail sales forecasting.
Achieve MAE <= 420. Use tabular ML (XGBoost/LightGBM), not ARIMA/Prophet.""",
        "hints": [
            "Lag features: lag_1, lag_7, lag_14, lag_28",
            "Rolling mean/std over 7-day window",
            "Calendar: day_of_week, is_weekend, month",
        ],
    },
    {
        "slug": "loan-default-pipeline",
        "title": "End-to-End ML Pipeline (Loan Default)",
        "difficulty": "medium",
        "category": "Finance",
        "concept_tag": "feature_engineering",
        "metric": "AUC_ROC",
        "points": 1200,
        "description": """Build sklearn Pipeline with ColumnTransformer for mixed feature types.
Achieve AUC-ROC >= 0.88. Handle numerical, low/high cardinality categoricals, ordinals.""",
        "hints": [
            "ColumnTransformer for different feature types",
            "TargetEncoder for high-cardinality categoricals",
            "No data leakage in the pipeline",
        ],
    },
    {
        "slug": "recommender-matrix-factorisation",
        "title": "Collaborative Filtering Recommender",
        "difficulty": "medium",
        "category": "Recommendations",
        "concept_tag": "collaborative_filtering",
        "metric": "RMSE",
        "points": 1200,
        "description": """Implement SVD-based collaborative filtering from scratch using numpy.
Achieve RMSE <= 0.95. No surprise/lightfm libraries allowed.""",
        "hints": [
            "Mean-centre the rating matrix first",
            "Truncate SVD to k=20 latent factors",
            "Clip predictions to valid rating range [1, 5]",
        ],
    },
    {
        "slug": "ensemble-stacking",
        "title": "Stacking Ensemble",
        "difficulty": "medium",
        "category": "Fundamentals",
        "concept_tag": "ensemble_learning",
        "metric": "AUC_ROC",
        "points": 1200,
        "description": """Build stacking ensemble achieving AUC >= 0.91. Level 0: LR, RF, GBM, KNN.
Level 1: LR on out-of-fold predictions. Implement manual CV stacking logic.""",
        "hints": [
            "Use 5-fold CV to generate level-0 OOF predictions",
            "Do NOT use sklearn StackingClassifier",
            "Meta-learner trained on OOF features only",
        ],
    },
    {
        "slug": "anomaly-detection-unsupervised",
        "title": "Unsupervised Anomaly Detection",
        "difficulty": "medium",
        "category": "Manufacturing",
        "concept_tag": "clustering",
        "metric": "AUC_ROC",
        "points": 1200,
        "description": """Industrial sensor readings. Train anomaly detector on normal data only.
Achieve AUC-ROC >= 0.88. Account for LOF limitations on new data.""",
        "hints": [
            "IsolationForest works well for unsupervised anomaly detection",
            "OneClassSVM trained on normal data only",
            "LOF requires refitting for new data — use predict on training set",
        ],
    },
    {
        "slug": "survival-analysis-churn",
        "title": "Survival Analysis for Customer Lifetime",
        "difficulty": "medium",
        "category": "Business",
        "concept_tag": "regression",
        "metric": "C_INDEX",
        "points": 1200,
        "description": """Subscription dataset with censored observations. Predict time to churn.
C-index >= 0.75. Use lifelines.CoxPHFitter or scikit-survival.""",
        "hints": [
            "Censoring means event=0 for still-active customers",
            "Cox proportional hazards model handles censoring",
            "Higher risk score = more likely to churn sooner",
        ],
    },
    # ==================== HARD (1600) — 12 problems ====================
    {
        "slug": "gradient-descent-scratch",
        "title": "Implement Gradient Descent from Scratch",
        "difficulty": "hard",
        "category": "Fundamentals",
        "concept_tag": "gradient_descent",
        "metric": "LOSS_CONVERGENCE",
        "points": 1600,
        "description": """Implement mini-batch SGD for logistic regression from scratch using only numpy.
Converge to loss <= 0.25 within 100 epochs. Include lr decay schedule.""",
        "starter_code": """import numpy as np

class LogisticRegressionSGD:
    def __init__(self, lr=0.01, epochs=100, batch_size=32):
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        self.W = None
        self.b = None
        self.losses = []

    def sigmoid(self, z):
        pass

    def compute_loss(self, y_pred, y_true):
        pass

    def compute_gradients(self, X, y_true, y_pred):
        pass

    def fit(self, X, y):
        pass

    def predict_proba(self, X):
        pass

    def predict(self, X, threshold=0.5):
        return (self.predict_proba(X) >= threshold).astype(int)
""",
        "hints": [
            "Implement binary cross-entropy loss",
            "Mini-batch sampling with batch_size=32",
            "Step decay: lr * 0.95 every 10 epochs",
        ],
    },
    {
        "slug": "kmeans-from-scratch",
        "title": "K-Means Clustering from Scratch",
        "difficulty": "hard",
        "category": "Fundamentals",
        "concept_tag": "clustering",
        "metric": "INERTIA+PURITY",
        "points": 1600,
        "description": """Implement K-Means from scratch with KMeans++ init. Vectorised E-step.
Inertia within 5% of sklearn. Cluster purity >= 0.85.""",
        "starter_code": """import numpy as np

class KMeans:
    def __init__(self, k=3, max_iter=300, tol=1e-4, random_state=42):
        self.k = k
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.centroids = None
        self.labels_ = None
        self.inertia_ = None
""",
        "hints": [
            "KMeans++ for better initialisation",
            "Vectorised distance computation in E-step",
            "Handle empty clusters by reassigning to furthest point",
        ],
    },
    {
        "slug": "decision-tree-scratch",
        "title": "Decision Tree from Scratch",
        "difficulty": "hard",
        "category": "Fundamentals",
        "concept_tag": "ensemble_learning",
        "metric": "ACCURACY",
        "points": 1600,
        "description": """Implement binary Decision Tree with Gini/entropy criteria, max_depth,
min_samples_split. Achieve >= 0.87 accuracy. Feature importances sum to 1.0.""",
        "hints": [
            "Search ALL features and ALL thresholds for best split",
            "Recursive tree building with stopping criteria",
            "Leaf prediction: majority class vote",
        ],
    },
    {
        "slug": "backpropagation-scratch",
        "title": "Neural Network Backpropagation from Scratch",
        "difficulty": "hard",
        "category": "Deep Learning",
        "concept_tag": "backpropagation",
        "metric": "ACCURACY",
        "points": 1600,
        "description": """2-layer NN: Input→Dense(64,ReLU)→Dense(32,ReLU)→Dense(1,Sigmoid).
Implement Adam optimiser from scratch. Target >= 0.90 accuracy.""",
        "starter_code": """import numpy as np

class NeuralNetwork:
    def __init__(self, layer_dims, lr=0.001):
        self.layer_dims = layer_dims
        self.lr = lr
        self.params = {}
        self.cache = {}
        self.grads = {}
        self.m = {}
        self.v = {}
        self.t = 0
        self._init_params()
""",
        "hints": [
            "He initialisation for ReLU layers",
            "Gradient clipping with clip_norm=1.0",
            "Implement Adam optimiser (not plain SGD)",
        ],
    },
    {
        "slug": "pca-from-scratch",
        "title": "PCA from Scratch + Reconstruction",
        "difficulty": "hard",
        "category": "Unsupervised",
        "concept_tag": "pca",
        "metric": "RECONSTRUCTION_ERROR",
        "points": 1600,
        "description": """Implement PCA from scratch. Reconstruction error within 1e-10 of sklearn.
Use np.linalg.eigh on covariance matrix. Explained variance ratios sum to 1.0.""",
        "hints": [
            "Mean-centre data before computing covariance",
            "Use 1/(n-1) for covariance matrix",
            "Sort eigenvalues descending, take top k components",
        ],
    },
    {
        "slug": "timeseries-lgbm-forecast",
        "title": "Multi-Step Time Series Forecasting",
        "difficulty": "hard",
        "category": "Forecasting",
        "concept_tag": "ensemble_learning",
        "metric": "MAPE",
        "points": 1600,
        "description": """Forecast next 168 hours of electricity demand. MAPE <= 4.5%.
LightGBM only with Direct Multi-Step strategy. TimeSeriesSplit for CV.""",
        "hints": [
            "One model per forecast horizon h=1..168",
            "Fourier features for weekly and daily seasonality",
            "Lag features: 1h, 24h, 168h",
        ],
    },
    {
        "slug": "bert-sentiment-finetuning",
        "title": "BERT Fine-tuning for Sentiment",
        "difficulty": "hard",
        "category": "NLP",
        "concept_tag": "transformers",
        "metric": "F1",
        "points": 1600,
        "description": """Fine-tune distilbert for 3-class financial sentiment. Macro F1 >= 0.82.
Gradient accumulation, early stopping. Must run on CPU in <= 5 minutes.""",
        "hints": [
            "Use distilbert-base-uncased for speed",
            "Learning rate 2e-5 with linear warmup",
            "Effective batch_size=32 with physical=8",
        ],
    },
    {
        "slug": "feature-store-pipeline",
        "title": "Feature Store Pipeline",
        "difficulty": "hard",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "CONSISTENCY",
        "points": 1600,
        "description": """Implement FeatureStore with backfill(), serve(), validate_consistency().
Point-in-time correctness — no future leakage. Train-serve consistency validation.""",
        "hints": [
            "Features computed as_of timestamp use only prior data",
            "backfill() and serve() must return identical values",
            "Track user_avg_spend_7d, user_txn_count_30d, etc.",
        ],
    },
    {
        "slug": "hyperparameter-optimisation",
        "title": "Bayesian Hyperparameter Optimisation",
        "difficulty": "hard",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "BEST_AUC",
        "points": 1600,
        "description": """Find best XGBoost hyperparameters using Optuna with exactly 50 trials.
AUC >= 0.935. Use TPESampler, StratifiedKFold, XGBoostPruningCallback.""",
        "hints": [
            "optuna.create_study with direction='maximize'",
            "Log each trial to a pandas DataFrame",
            "Search n_estimators, max_depth, learning_rate, subsample, etc.",
        ],
    },
    {
        "slug": "production-inference",
        "title": "Production Inference Under Constraints",
        "difficulty": "hard",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "LATENCY+ACCURACY",
        "points": 1600,
        "description": """Deploy fraud model with SLA: p99 <= 5ms, throughput >= 5000 req/s,
memory <= 50MB. AUC within 0.02 of original. Apply quantisation, pruning, feature selection.""",
        "hints": [
            "Model quantisation (int8 for leaf weights)",
            "Remove features with importance < 1%",
            "Vectorised batch prediction for throughput",
        ],
    },
    {
        "slug": "drift-detection",
        "title": "Data & Concept Drift Detection",
        "difficulty": "hard",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "F1+DETECTION_RATE",
        "points": 1600,
        "description": """Implement drift monitoring: PSI for feature drift, KL divergence for
prediction drift, accuracy/F1 for concept drift. Catch >= 80% of drift days, FPR <= 15%.""",
        "hints": [
            "PSI > 0.2 indicates significant feature drift",
            "Population Stability Index formula: sum((actual% - expected%) * ln(actual%/expected%))",
            "Monitor daily batches against reference distribution",
        ],
    },
    {
        "slug": "model-explainability",
        "title": "SHAP + LIME Explainability",
        "difficulty": "hard",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "EXPLANATION_QUALITY",
        "points": 1600,
        "description": """Audit credit scoring model: SHAP values, fairness metrics (demographic parity,
equal opportunity), LIME counterfactuals, model card JSON. EU AI Act compliance.""",
        "hints": [
            "TreeExplainer for SHAP on tree models",
            "Demographic parity difference <= 0.05 threshold",
            "Counterfactual: minimum feature changes to flip prediction",
        ],
    },
    # ==================== EXPERT (2000) — 9 problems ====================
    {
        "slug": "asymmetric-cost-loss",
        "title": "Custom Loss Function (Asymmetric Cost)",
        "difficulty": "expert",
        "category": "Finance",
        "concept_tag": "gradient_descent",
        "metric": "CUSTOM_COST",
        "points": 2000,
        "description": """Implement asymmetric cross-entropy in XGBoost: FN_weight=10, FP_weight=1.
Custom objective with gradient and hessian. Total cost <= 1500 on test set.""",
        "hints": [
            "Custom objective: def asymmetric_loss(y_pred, dtrain) → (grad, hess)",
            "False negatives cost 10x more than false positives",
            "Implement custom evaluation metric for XGBoost",
        ],
    },
    {
        "slug": "transformer-attention-scratch",
        "title": "Transformer Self-Attention from Scratch",
        "difficulty": "expert",
        "category": "Deep Learning",
        "concept_tag": "transformers",
        "metric": "LOSS",
        "points": 2000,
        "description": """Implement multi-head self-attention and Transformer encoder block from scratch
using numpy. Match PyTorch nn.MultiheadAttention within 1e-4 tolerance.""",
        "hints": [
            "Scaled dot-product: softmax(QK^T / sqrt(d_k)) @ V",
            "8 heads, d_model=512, d_ff=2048",
            "Layer normalisation with residual connections",
        ],
    },
    {
        "slug": "federated-learning-simulation",
        "title": "Federated Learning (FedAvg)",
        "difficulty": "expert",
        "category": "Advanced",
        "concept_tag": "mlops",
        "metric": "GLOBAL_ACCURACY",
        "points": 2000,
        "description": """Implement FedAvg across 10 clients with non-IID Dirichlet partitioning.
20 communication rounds, 5 local epochs. Global accuracy >= 0.82 on MNIST.""",
        "hints": [
            "Server aggregates: W_global = sum(n_k/N * W_k)",
            "Sample 30% of clients each round",
            "Track communication cost per round",
        ],
    },
    {
        "slug": "online-learning-adaptive",
        "title": "Online Learning with Adaptive Drift Response",
        "difficulty": "expert",
        "category": "Advanced",
        "concept_tag": "mlops",
        "metric": "CUMULATIVE_REGRET",
        "points": 2000,
        "description": """Streaming data with 4 abrupt concept drift points. Implement ADWIN drift detector
and online classifier. Cumulative regret <= 4200 (vs naive ~7500).""",
        "hints": [
            "ADWIN: detect drift when sub-window means differ significantly",
            "Reset model or use weighted ensemble on drift detection",
            "River library allowed for this problem",
        ],
    },
    {
        "slug": "uplift-modelling",
        "title": "Causal ML: Uplift Modelling",
        "difficulty": "expert",
        "category": "Business",
        "concept_tag": "causal_ml",
        "metric": "QINI_SCORE",
        "points": 2000,
        "description": """Marketing A/B test data. Implement T-learner, S-learner, X-learner.
Qini coefficient >= 0.28. Identify top 20% persuadable customers.""",
        "hints": [
            "Uplift = P(Y=1|X,T=1) - P(Y=1|X,T=0)",
            "T-learner: separate models for treated and control",
            "Qini curve measures incremental value of targeting",
        ],
    },
    {
        "slug": "graph-neural-network",
        "title": "Graph Neural Network for Fraud Detection",
        "difficulty": "expert",
        "category": "Finance",
        "concept_tag": "neural_networks",
        "metric": "AUC_ROC",
        "points": 2000,
        "description": """2-layer GCN using PyTorch Geometric for transaction graph fraud detection.
AUC-ROC >= 0.91 vs tabular XGBoost baseline 0.84. Focal loss for class imbalance.""",
        "hints": [
            "GraphConv layers with message passing",
            "NeighborLoader for mini-batch training",
            "Fraud operates in rings — graph structure matters",
        ],
    },
    {
        "slug": "neural-architecture-search",
        "title": "Differentiable Neural Architecture Search (DARTS)",
        "difficulty": "expert",
        "category": "Deep Learning",
        "concept_tag": "neural_networks",
        "metric": "ACCURACY+EFFICIENCY",
        "points": 2000,
        "description": """Simplified DARTS with mixed operations and bi-level optimisation.
Discovered architecture >= 92% on CIFAR-10 subset with < 0.5M parameters.""",
        "hints": [
            "Mixed operation: sum(softmax(alpha_k) * op_k(x))",
            "Inner loop: update W, outer loop: update alpha",
            "Derive discrete architecture by argmax(alpha)",
        ],
    },
    {
        "slug": "rl-contextual-bandit",
        "title": "Contextual Bandit for Personalised Recommendations",
        "difficulty": "expert",
        "category": "Recommendations",
        "concept_tag": "reinforcement_learning",
        "metric": "CUMULATIVE_REWARD",
        "points": 2000,
        "description": """Netflix-style contextual bandit. Implement LinUCB, Thompson Sampling,
epsilon-greedy. Adapt after reward matrix shift at round 5000. Efficiency >= 0.88.""",
        "hints": [
            "LinUCB: UCB_a(x) = theta_a.T @ x + alpha * sqrt(x.T @ A_a^-1 @ x)",
            "CUSUM test to detect non-stationary shift",
            "Balance exploration vs exploitation",
        ],
    },
    {
        "slug": "e2e-ml-system",
        "title": "Production ML System: Design + Implement",
        "difficulty": "expert",
        "category": "MLOps",
        "concept_tag": "mlops",
        "metric": "SYSTEM_SCORE",
        "points": 2000,
        "description": """Complete ML system: feature pipeline (batch + real-time), two-tower model,
FAISS ANN index, LightGBM re-ranker, FastAPI serving (<=50ms), monitoring, A/B test.""",
        "hints": [
            "Feature consistency between training and serving",
            "Two-tower: user tower + item tower → dot product",
            "Fallback to popularity for cold-start users",
        ],
    },
]
