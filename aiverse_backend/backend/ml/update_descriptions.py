"""
Update problem descriptions with comprehensive, educational content.

This script updates all problems with detailed descriptions explaining:
- Real-world context
- Dataset meaning
- Task type
- What to return
- Metrics used
- Submission threshold
"""

from ml.models import Problem

# Dictionary of slug -> new description
PROBLEM_DESCRIPTIONS = {
    'iris-species-classification': """
# Iris Species Classification

## Real-World Context
The Iris dataset is one of the most famous datasets in machine learning, collected by Ronald Fisher in 1936. 
It contains measurements of iris flowers from three different species and is used to demonstrate classification algorithms.

## Dataset
You are given measurements of iris flowers:
- **Features (4):**
  - Sepal length (cm)
  - Sepal width (cm)
  - Petal length (cm)
  - Petal width (cm)

- **Target:** Flower species (0=setosa, 1=versicolor, 2=virginica)

## Your Task
Build a **multi-class classification model** that predicts the iris species from its measurements.

Your function must:
1. Accept training data: `X_train` (features), `y_train` (species)
2. Train a classifier on the training data
3. Make predictions on test data: `X_test`
4. Return predictions as a 1D array

## Example Code
```python
def train_and_predict(X_train, y_train, X_test):
    from sklearn.linear_model import LogisticRegression
    
    model = LogisticRegression(max_iter=200, random_state=42)
    model.fit(X_train, y_train)
    return model.predict(X_test)
```

## Evaluation Metric
- **Metric:** Accuracy (higher is better)
- **Formula:** (correct predictions) / (total predictions)
- **Threshold:** Must achieve ≥ 0.75 accuracy to submit

## What Makes a Good Solution
- Handles multi-class classification correctly
- Uses appropriate regularization for small dataset
- Achieves accuracy above 75%
- Returns predictions in correct format (1D array with species indices)

## Common Mistakes
- Forgetting to fit the model before predicting
- Returning probabilities instead of class labels
- Using incorrect feature scaling
""".strip(),

    'spam-detection': """
# Spam Email Detection

## Real-World Context
Email spam is a major problem affecting billions of users globally. Machine learning models help filter 
unwanted emails by learning patterns in spam vs legitimate messages. This dataset contains real spam 
classification data.

## Dataset
You are given email messages represented as feature vectors:
- **Features (48):** TF-IDF or token frequencies from email text
- **Target:** Binary classification (0=legitimate, 1=spam)
- **Size:** ~4600 emails in training set

## Your Task
Build a **binary classification model** that identifies spam emails with high precision.

Your function must:
1. Accept training data: `X_train`, `y_train`
2. Train a classifier on the training data
3. Predict spam/not-spam for test emails
4. Return predictions as a 1D binary array (0 or 1)

## Example Code
```python
def train_and_predict(X_train, y_train, X_test):
    from sklearn.naive_bayes import MultinomialNB
    
    model = MultinomialNB()
    model.fit(X_train, y_train)
    return model.predict(X_test)
```

## Evaluation Metric
- **Metric:** F1 Score (weighted harmonic mean of precision and recall)
- **Range:** 0-1 (higher is better)
- **Threshold:** Must achieve ≥ 0.80 F1 score to submit
- **Why F1:** Better than accuracy for imbalanced datasets

## What Makes a Good Solution
- Handles class imbalance appropriately
- Uses efficient algorithms suitable for text features
- Achieves F1 score ≥ 0.80
- Returns clean binary predictions (0 or 1)

## Common Mistakes
- Using only accuracy (misses class imbalance)
- Not handling sparse feature vectors correctly
- Overfitting to training data
""".strip(),

    'customer-churn-prediction': """
# Customer Churn Prediction

## Real-World Context
Predicting customer churn is critical for subscription-based businesses. Identifying customers likely to 
leave allows companies to intervene with retention strategies. This dataset contains customer behavior 
metrics from a telecom company.

## Dataset
You are given customer account information and behavior metrics:
- **Features (19):** Usage patterns, contract type, payment method, etc.
- **Target:** Binary classification (0=stays, 1=churns)
- **Size:** ~7000 customers

## Your Task
Build a **binary classification model** that predicts which customers will churn.

Your function must:
1. Accept training data: `X_train`, `y_train`
2. Learn patterns of churning vs loyal customers
3. Predict churn probability for test customers
4. Return predictions as a 1D binary array

## Example Code
```python
def train_and_predict(X_train, y_train, X_test):
    from sklearn.ensemble import RandomForestClassifier
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model.predict(X_test)
```

## Evaluation Metric
- **Metric:** F1 Score (considers both precision and recall)
- **Range:** 0-1 (higher is better)
- **Threshold:** Must achieve ≥ 0.75 F1 score to submit
- **Why F1:** Uneven class distribution requires balanced metric

## What Makes a Good Solution
- Addresses class imbalance (fewer churners than loyal customers)
- Uses ensemble methods for better generalization
- Achieves F1 score ≥ 0.75
- Handles mixed feature types (numerical and categorical)

## Common Mistakes
- Ignoring class imbalance
- Not properly encoding categorical features
- Using only accuracy metric
- Overfitting to training data
""".strip(),

    'credit-risk-prediction': """
# Credit Risk Prediction

## Real-World Context
Banks and financial institutions use credit scoring to assess the risk of lending money. A reliable 
risk prediction model helps minimize defaults and improve lending decisions. This dataset contains 
application and financial information of credit applicants.

## Dataset
You are given applicant financial and demographic information:
- **Features (20):** Income, credit history, loan amount, employment status, etc.
- **Target:** Binary classification (0=low risk/approved, 1=high risk/rejected)
- **Size:** ~1000 applications

## Your Task
Build a **binary classification model** that identifies high-risk credit applicants.

Your function must:
1. Accept training data: `X_train`, `y_train`
2. Learn patterns that distinguish risk levels
3. Predict risk for new applications
4. Return predictions as a 1D binary array

## Example Code
```python
def train_and_predict(X_train, y_train, X_test):
    from sklearn.linear_model import LogisticRegression
    
    model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    return model.predict(X_test)
```

## Evaluation Metric
- **Metric:** Accuracy (percentage correct)
- **Range:** 0-1 (higher is better)
- **Threshold:** Must achieve ≥ 0.75 accuracy to submit
- **Note:** In real banking, precision/recall would matter more, but for this exercise, accuracy is used

## What Makes a Good Solution
- Handles imbalanced training data appropriately
- Uses logistic regression or ensemble methods
- Achieves ≥ 0.75 accuracy
- Properly scales numerical features
- Handles missing values if present

## Common Mistakes
- Not using class balancing
- Skipping feature preprocessing
- Using inappropriate algorithms
- Not validating on held-out test set
""".strip(),

    'house-price-prediction': """
# House Price Prediction

## Real-World Context
Real estate valuation is essential for buyers, sellers, and financial institutions. Machine learning 
models can predict house prices based on property characteristics, helping inform pricing decisions. 
This dataset contains housing information with sale prices.

## Dataset
You are given property characteristics and historical sale prices:
- **Features (13):** Square footage, rooms, location, age, amenities, etc.
- **Target:** House sale price (continuous numerical value in thousands)
- **Size:** ~500 houses

## Your Task
Build a **regression model** that predicts house prices from property features.

Your function must:
1. Accept training data: `X_train`, `y_train` (prices in thousands)
2. Learn the relationship between features and prices
3. Predict prices for test properties
4. Return predictions as a 1D array of numerical values

## Example Code
```python
def train_and_predict(X_train, y_train, X_test):
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LinearRegression()
    model.fit(X_train_scaled, y_train)
    return model.predict(X_test_scaled)
```

## Evaluation Metric
- **Metric:** RMSE - Root Mean Squared Error (lower is better)
- **Formula:** sqrt(mean((y_true - y_pred)^2))
- **Threshold:** Must achieve ≤ 50 RMSE to submit
- **Unit:** Thousands of dollars (e.g., RMSE=30 means ±$30,000 error)

## What Makes a Good Solution
- Properly scales features before training
- Uses regression algorithms (not classification)
- Achieves RMSE ≤ 50 (thousand dollars)
- Handles feature engineering appropriately
- Uses cross-validation for robust estimates

## Common Mistakes
- Using classification model instead of regression
- Not scaling features (huge performance loss)
- Returning classification classes instead of numerical values
- Ignoring outliers and extreme prices
- Not validating predictions are reasonable
""".strip(),
}


def update_descriptions():
    """Update all problem descriptions."""
    for slug, new_description in PROBLEM_DESCRIPTIONS.items():
        try:
            problem = Problem.objects.get(slug=slug)
            problem.description = new_description
            problem.save(update_fields=['description'])
            print(f"✓ Updated: {slug}")
        except Problem.DoesNotExist:
            print(f"✗ Not found: {slug}")


if __name__ == '__main__':
    update_descriptions()
    print("\n✓ All problem descriptions updated!")
