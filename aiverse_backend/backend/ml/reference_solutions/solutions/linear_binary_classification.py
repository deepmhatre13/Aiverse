"""Reference solution — INTERNAL ONLY, NEVER EXPOSE TO USERS"""

def train_and_predict(X_train, y_train, X_test):
    from sklearn.linear_model import LogisticRegression
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    return model.predict(X_test)
