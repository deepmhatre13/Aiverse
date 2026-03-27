"""
Update problem descriptions to production-grade structured format.

Every description includes:
1. Real-World Context
2. Dataset Explanation  
3. Task Definition
4. Function Contract
5. Evaluation Metric
6. Submission Threshold
7. Common Mistakes
"""

from ml.models_ml import Problem

PROBLEM_DESCRIPTIONS = {
    'iris-species-classification': """# Iris Species Classification

## Quick Summary
- **Task Type:** Multi-class Classification
- **Metric:** Accuracy (higher is better)
- **Threshold:** ≥ 0.75
- **Dataset Size:** 120 training, 30 test samples

## Real-World Context

The Iris dataset is one of the most famous datasets in machine learning, collected by Ronald Fisher in 1936. It demonstrates how botanical measurements can classify plant species. In the real world, similar classification problems appear in:
- **Agriculture:** Classifying crop varieties by morphological traits
- **Ecology:** Species identification from physical measurements
- **Quality control:** Categorizing products by manufacturing metrics

This problem teaches fundamental classification principles that apply to medical diagnostics, fraud detection, and recommendation systems.

## Dataset Explanation

Each row represents measurements of **one iris flower**:
- **Sepal length:** Outer leaf-like structure, measured in centimeters
- **Sepal width:** Width of the same outer structure
- **Petal length:** Inner flower petal, measured in centimeters
- **Petal width:** Width of the inner petal

The **target variable** is the iris species:
- **0 = Setosa:** Small-petaled species
- **1 = Versicolor:** Medium-petaled species
- **2 = Virginica:** Large-petaled species

The dataset contains 120 training samples and 30 test samples.

## Task Definition

You must build a **multi-class classification model** that learns patterns from the training data and predicts which of the 3 iris species a flower belongs to based on its measurements.

This is **classification** (not regression) because:
- Output is a discrete category (0, 1, or 2)
- Not a continuous numerical prediction
- Each prediction is a class label

## Function Contract

```python
def train_and_predict(X_train, y_train, X_test):
    # X_train: array of shape (120, 4) - training features
    # y_train: array of shape (120,) - training labels (0, 1, or 2)
    # X_test: array of shape (30, 4) - test features
    
    # Your code here: train model, make predictions
    
    # MUST return: predictions for X_test
    # Shape: (30,) - exactly 30 predictions
    # Values: integers 0, 1, or 2 (class labels)
    return predictions
```

**Critical Rules:**
- Accept exactly 3 arguments: X_train, y_train, X_test
- Return predictions only (1D array of integers)
- Do NOT print anything
- Do NOT save files
- Import only inside function: numpy, pandas, sklearn

**Valid Code Pattern:**
```python
def train_and_predict(X_train, y_train, X_test):
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train classifier
    model = LogisticRegression(max_iter=200)
    model.fit(X_train_scaled, y_train)
    
    # Return predictions (class labels, not probabilities)
    return model.predict(X_test_scaled)
```

## Evaluation Metric

**Metric:** Accuracy

**Definition:** Percentage of correct predictions
```
accuracy = (correct_predictions) / (total_predictions)
```

**Why Accuracy?**
- All 3 species are equally represented (balanced dataset)
- All misclassifications have equal cost
- Simple, interpretable metric

**Higher is better:** Score of 0.90 is better than 0.80

## Submission Threshold

**Minimum Score:** 0.75 (75% accuracy)

**What happens if you meet the threshold:**
- ✅ Submission is **ACCEPTED**
- ✅ You appear on leaderboard
- ✅ Your rank is calculated

**What happens if you're below the threshold:**
- ❌ Submission is **REJECTED**
- ❌ You do NOT appear on leaderboard
- ❌ Your code is saved but not ranked

**Example:**
- Score 0.80 → ✅ ACCEPTED (above 0.75)
- Score 0.75 → ✅ ACCEPTED (meets exactly)
- Score 0.74 → ❌ REJECTED (below threshold)

## Common Mistakes

**1. Returning probabilities instead of class labels**
```python
# ❌ WRONG
return model.predict_proba(X_test)  # Returns [0.1, 0.7, 0.2], etc

# ✅ CORRECT
return model.predict(X_test)  # Returns 0, 1, or 2
```

**2. Not scaling features**
```python
# ❌ WRONG - features have different ranges
model.fit(X_train, y_train)  # Sepal width [2-4] dominates petal length [1-7]

# ✅ CORRECT - scale to comparable ranges
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
model.fit(X_train_scaled, y_train)
```

**3. Shape mismatch in return value**
```python
# ❌ WRONG - returning 2D array
return model.predict(X_test).reshape(-1, 1)  # Shape (30, 1)

# ✅ CORRECT - return 1D array
return model.predict(X_test)  # Shape (30,)
```

**4. Forgetting to fit before predicting**
```python
# ❌ WRONG - model not trained
model = LogisticRegression()
return model.predict(X_test)  # Error: model not fitted

# ✅ CORRECT - fit first
model.fit(X_train, y_train)
return model.predict(X_test)
```

**5. Data leakage - fitting scaler on test data**
```python
# ❌ WRONG - test data statistics leak into training
scaler = StandardScaler()
X_test_scaled = scaler.fit_transform(X_test)  # Should not fit on test
X_train_scaled = scaler.transform(X_train)

# ✅ CORRECT - fit only on training data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Only transform, don't fit
```

**6. Not handling class imbalance (even though iris is balanced)**
```python
# ⚠️ For future imbalanced problems:
model = LogisticRegression(class_weight='balanced')  # Handles class imbalance
```

**7. Using the training set accuracy instead of test set**
The platform evaluates on the **test set**, not training set. Overfitting gives false confidence:
```python
# ❌ WRONG THINKING
accuracy_on_train = model.score(X_train, y_train)  # Often 99%+, misleading

# ✅ CORRECT
# Platform uses X_test and y_test (hidden from you)
# Your code makes predictions on X_test only
return model.predict(X_test)
```
""".strip(),

    'spam-detection': """# Spam Email Detection

## Quick Summary
- **Task Type:** Binary Classification
- **Metric:** F1 Score (higher is better)
- **Threshold:** ≥ 0.80
- **Dataset Size:** 3000+ training samples

## Real-World Context

Email spam is a critical problem affecting billions of users globally. Spam costs businesses billions in lost productivity and enables phishing attacks. Major email providers (Gmail, Outlook, Yahoo) use machine learning classifiers to automatically filter spam.

In this problem, you build a classifier using the **SpamBase dataset**, which contains real email features extracted from spam and legitimate messages. Your model will learn patterns that distinguish spam from legitimate email.

Real-world impact:
- **Wrong classification costs:** False positives (legitimate email marked spam) cause worse user experience than false negatives (spam reaching inbox)
- **Dataset imbalance:** Fewer spam messages in datasets than legitimate messages
- **Feature types:** Text-based features (word frequencies), sender reputation, etc.

## Dataset Explanation

Each row represents **one email message** summarized as 48 numerical features:

**Feature Groups:**
- **Word frequencies:** How often certain words appear (e.g., "free", "money", "click")
- **Character frequencies:** How often special characters appear (e.g., "$", "!")
- **Capital letter statistics:** Average length of consecutive capitals
- **Domain reputation:** Features derived from sender domain

**Target Variable:**
- **0 = Legitimate email:** Normal, expected message
- **1 = Spam:** Unsolicited, malicious, or promotional message

The dataset is **imbalanced:** ~60% legitimate, ~40% spam. This means naïve accuracy (always predicting 0) appears artificially high.

## Task Definition

You must build a **binary classification model** that learns spam patterns and predicts whether an email is legitimate (0) or spam (1).

This is **classification** because:
- Output is binary: spam or not spam
- Not a continuous score
- Each prediction is a category

**Why not just use accuracy?**
With 60% legitimate emails, a model that always predicts "0" gets 60% accuracy but misses all spam. We use **F1 Score** instead, which balances precision (avoiding false spam alerts) and recall (catching all spam).

## Function Contract

```python
def train_and_predict(X_train, y_train, X_test):
    # X_train: array of shape (3000+, 48) - training email features
    # y_train: array of shape (3000+,) - training labels (0 or 1)
    # X_test: array of shape (N, 48) - test email features
    
    # Your code here: train model, make predictions
    
    # MUST return: predictions for X_test
    # Shape: (N,) - one prediction per test email
    # Values: 0 (legitimate) or 1 (spam)
    return predictions
```

**Critical Rules:**
- Accept exactly 3 arguments
- Return binary predictions (0 or 1)
- Do NOT print results
- Import only inside function: numpy, pandas, sklearn

## Evaluation Metric

**Metric:** F1 Score (weighted for imbalanced classes)

**Definition:** Harmonic mean of precision and recall
```
Precision = TP / (TP + FP)  [when we predict spam, how often correct?]
Recall = TP / (TP + FN)     [when email is spam, do we catch it?]
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Why F1 instead of Accuracy?**
- Accuracy ignores class imbalance
- F1 balances:
  - **Precision:** Minimize false spam alerts (users annoyed)
  - **Recall:** Maximize spam caught (users annoyed by more)
- F1 is real-world metric used by email providers

**Higher is better:** F1 of 0.85 is better than 0.75

## Submission Threshold

**Minimum Score:** 0.80 (80% F1)

**What happens if you meet the threshold:**
- ✅ Submission ACCEPTED
- ✅ You appear on leaderboard
- ✅ Ranked against other solutions

**What happens if below the threshold:**
- ❌ Submission REJECTED
- ❌ Code saved but not ranked

**Example:**
- F1 = 0.82 → ✅ ACCEPTED
- F1 = 0.80 → ✅ ACCEPTED (meets exactly)
- F1 = 0.79 → ❌ REJECTED

## Common Mistakes

**1. Ignoring class imbalance**
```python
# ❌ WRONG - model biased toward majority class
model = LogisticRegression()
model.fit(X_train, y_train)

# ✅ CORRECT - balance classes
model = LogisticRegression(class_weight='balanced')
model.fit(X_train, y_train)
```

**2. Using Accuracy instead of F1**
```python
# ❌ WRONG - doesn't catch imbalance
accuracy = (TP + TN) / (TP + FP + TN + FN)

# ✅ CORRECT - use F1
from sklearn.metrics import f1_score
f1 = f1_score(y_true, y_pred, average='weighted')
```

**3. Returning probabilities instead of class labels**
```python
# ❌ WRONG
return model.predict_proba(X_test)  # Returns [0.3, 0.7], etc

# ✅ CORRECT
return model.predict(X_test)  # Returns 0 or 1
```

**4. Not handling sparse features**
Email features are often sparse (many zeros). Some models handle this better:
```python
# ⚠️ Consider algorithm choice
model = LogisticRegression()  # Good for sparse
# vs
model = KNeighborsClassifier()  # Bad for sparse (distance uninformative)
```

**5. No feature scaling (depends on algorithm)**
```python
# ⚠️ Some algorithms don't need scaling:
LogisticRegression()  # Naturally handles different scales
# But some do:
KNeighborsClassifier()  # Needs scaled features
```

**6. Overfitting to training set**
```python
# ❌ WRONG - model memorizes training patterns
model = GradientBoostingClassifier(n_estimators=10000, depth=20)

# ✅ CORRECT - regularization prevents overfitting
model = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
```
""".strip(),

    'customer-churn-prediction': """# Customer Churn Prediction

## Quick Summary
- **Task Type:** Binary Classification
- **Metric:** F1 Score (higher is better)
- **Threshold:** ≥ 0.75
- **Dataset Size:** 7000 customer records

## Real-World Context

Customer churn (customers leaving a service) is a critical business metric. For subscription-based companies (SaaS, telecoms, streaming), 5% churn monthly means 60% of customers leave annually.

Real-world impact:
- **Cost:** Acquiring new customers costs 5-25x more than retention
- **Intervention:** Identifying at-risk customers enables targeted retention offers
- **Business decision:** Marketing teams use predictions to allocate retention budgets
- **Fairness:** Models must not discriminate by protected attributes

This problem uses a telecom customer dataset. Your model predicts which customers are likely to churn, enabling proactive intervention.

## Dataset Explanation

Each row represents **one customer account** with these feature groups:

**Account Information:**
- Contract length (month-to-month, 1-year, 2-year)
- Tenure: Months as a customer

**Services:**
- Phone service, internet service, online security, backup, etc.

**Demographics:**
- Senior citizen status
- Partner status
- Dependent status

**Billing:**
- Monthly charges
- Total charges
- Payment method

**Target Variable:**
- **0 = Stayed:** Customer did not churn
- **1 = Churned:** Customer left the service

The dataset is **imbalanced:** ~73% stayed, ~27% churned.

## Task Definition

You must build a **binary classification model** that predicts whether a customer will churn (leave) based on their account characteristics.

This is a real-world problem because:
- Business has real costs for wrong predictions
- False positives (predicting churn but customer stays) waste retention budget
- False negatives (missing actual churn) cause lost revenue
- Models must be explainable for human review

## Function Contract

```python
def train_and_predict(X_train, y_train, X_test):
    # X_train: array of shape (5000+, N_features) - training customer data
    # y_train: array of shape (5000+,) - training labels (0 or 1)
    # X_test: array of shape (N, N_features) - test customer data
    
    # Your code: train model, make predictions
    
    # MUST return: predictions for X_test
    # Shape: (N,) - one per customer
    # Values: 0 (stays) or 1 (churns)
    return predictions
```

## Evaluation Metric

**Metric:** F1 Score (weighted)

**Why F1?**
- Balances false positives and false negatives
- Class imbalance (73/27) requires F1, not accuracy
- Aligns with business cost of wrong predictions

**Higher is better**

## Submission Threshold

**Minimum Score:** 0.75

**Acceptance:**
- F1 ≥ 0.75 → ✅ ACCEPTED
- F1 < 0.75 → ❌ REJECTED

## Common Mistakes

**1. Using Accuracy with imbalanced data**
Always predict 0 → 73% accuracy but catches 0 churn.

**2. Not encoding categorical features**
```python
# ❌ WRONG - strings can't be used directly
model.fit(X_train, y_train)  # Error if X_train has strings

# ✅ CORRECT - encode categories
from sklearn.preprocessing import LabelEncoder
encoder = LabelEncoder()
X_train_encoded = X_train.copy()
X_train_encoded['contract'] = encoder.fit_transform(X_train['contract'])
```

**3. Data leakage in preprocessing**
```python
# ❌ WRONG - fitting encoder on test data
encoder = LabelEncoder()
X_test_encoded['contract'] = encoder.fit_transform(X_test['contract'])

# ✅ CORRECT - fit only on training
encoder.fit(X_train['contract'])  # Learn categories from training
X_test_encoded['contract'] = encoder.transform(X_test['contract'])  # Apply to test
```

**4. Including non-predictive features**
Some features might leak information about the target or be uninformative.

**5. Not handling missing values**
```python
# ❌ WRONG - models can't handle NaN
model.fit(X_train, y_train)  # Error if X_train has NaN

# ✅ CORRECT - impute or drop
X_train_clean = X_train.fillna(X_train.mean())  # Fill with mean
# or
X_train_clean = X_train.dropna()  # Remove rows with NaN
```
""".strip(),

    'house-price-prediction': """# House Price Prediction

## Quick Summary
- **Task Type:** Regression
- **Metric:** RMSE - Root Mean Squared Error (lower is better)
- **Threshold:** ≤ 50 (thousand dollars)
- **Dataset Size:** 500 house records

## Real-World Context

Real estate valuation is essential for:
- **Buyers:** Knowing fair market price
- **Sellers:** Competitive pricing
- **Banks:** Mortgage lending decisions
- **Tax assessment:** Property tax calculations

Machine learning models predict house prices based on characteristics (location, size, age, amenities), providing data-driven valuations faster than human appraisers.

This problem uses a housing dataset with median house prices (in thousands of dollars). Your model learns the relationship between features and price.

## Dataset Explanation

Each row represents **one house** with these features:

**Location & Geography:**
- City/region indicators
- Proximity to urban centers

**Physical Characteristics:**
- Number of rooms
- House age
- Square footage

**Building Quality:**
- Construction type
- Condition

**Target Variable:**
- House price in **thousands of dollars**
- Example: 350 means $350,000
- Continuous numerical value

## Task Definition

You must build a **regression model** that predicts house prices from property characteristics.

This is **regression** (not classification) because:
- Output is continuous (any value like 234.5)
- Not a discrete category
- Price varies smoothly with features

**Regression vs Classification:**
```
❌ WRONG for this problem: predict "expensive" or "cheap"
✅ CORRECT for this problem: predict exact price like $347,500
```

## Function Contract

```python
def train_and_predict(X_train, y_train, X_test):
    # X_train: array of shape (350, N_features) - training house features
    # y_train: array of shape (350,) - training prices (in thousands)
    # X_test: array of shape (150, N_features) - test house features
    
    # Your code: train model, make predictions
    
    # MUST return: predictions for X_test
    # Shape: (150,) - one price per house
    # Values: floats (e.g., 234.5 for $234,500)
    return predictions
```

## Evaluation Metric

**Metric:** RMSE - Root Mean Squared Error

**Definition:**
```
RMSE = sqrt(mean((y_true - y_pred)^2))
```

**Interpretation:**
- RMSE = 50 means predictions are off by ~$50,000 on average
- RMSE = 20 means predictions are off by ~$20,000 on average
- Measured in thousands of dollars (same units as price)

**Lower is better:** RMSE of 25 is better than RMSE of 50

**Why RMSE?**
- Penalizes large errors more (squaring)
- Same units as target (dollars)
- Standard metric in regression
- Interpretable: RMSE of 50 = ±$50k average error

## Submission Threshold

**Maximum RMSE:** 50 (thousand dollars = $50,000)

**Acceptance:**
- RMSE ≤ 50 → ✅ ACCEPTED
- RMSE > 50 → ❌ REJECTED

**Example:**
- RMSE = 45 → ✅ ACCEPTED (within threshold)
- RMSE = 50 → ✅ ACCEPTED (meets exactly)
- RMSE = 52 → ❌ REJECTED (exceeds threshold)

## Common Mistakes

**1. Using classification model for regression**
```python
# ❌ WRONG - returns discrete classes
from sklearn.tree import DecisionTreeClassifier
model = DecisionTreeClassifier()  # Wrong model type

# ✅ CORRECT - returns continuous values
from sklearn.tree import DecisionTreeRegressor
model = DecisionTreeRegressor()  # Correct for regression
```

**2. Returning class labels instead of continuous values**
```python
# ❌ WRONG
return [1, 0, 1, 0]  # Only discrete values

# ✅ CORRECT
return [234.5, 489.2, 156.7, 412.1]  # Continuous values
```

**3. Not scaling features**
```python
# ❌ WRONG - large-scale features dominate
model = LinearRegression()
# Square footage [1000-5000] dominates age [1-100]

# ✅ CORRECT - scale to comparable ranges
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

**4. No regularization → overfitting**
```python
# ❌ WRONG - model memorizes training noise
model = LinearRegression()  # No regularization
# or
model = DecisionTreeRegressor(max_depth=50)  # Too flexible

# ✅ CORRECT - add regularization
model = Ridge(alpha=1.0)  # L2 regularization
# or
model = DecisionTreeRegressor(max_depth=5)  # Limited depth
```

**5. Ignoring outliers**
```python
# ⚠️ Outliers (very expensive houses) can hurt RMSE
# Consider:
# - Removing extreme outliers
# - Using robust_scale instead of StandardScaler
# - Using algorithms less sensitive to outliers (tree-based)
```

**6. Data leakage in preprocessing**
```python
# ❌ WRONG - fitting scaler on test data
scaler = StandardScaler()
X_test_scaled = scaler.fit_transform(X_test)  # Shouldn't fit on test
X_train_scaled = scaler.transform(X_train)

# ✅ CORRECT - fit only on training data
scaler.fit(X_train)  # Learn statistics from training only
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

**7. Predicting outside reasonable range**
```python
# ⚠️ Your model might predict negative prices or absurdly high values
# Consider clipping predictions to reasonable range:
predictions = np.clip(predictions, min_house_price, max_house_price)
# But be careful: clipping increases RMSE if wrong
```
""".strip(),
}


def update_descriptions():
    """Update all problem descriptions in database."""
    for slug, description in PROBLEM_DESCRIPTIONS.items():
        try:
            problem = Problem.objects.get(slug=slug)
            problem.description = description
            problem.save(update_fields=['description'])
            print(f"✓ Updated: {slug}")
        except Problem.DoesNotExist:
            print(f"✗ Not found: {slug}")


if __name__ == '__main__':
    update_descriptions()
    print("\n✓ All problem descriptions updated to production-grade format!")
