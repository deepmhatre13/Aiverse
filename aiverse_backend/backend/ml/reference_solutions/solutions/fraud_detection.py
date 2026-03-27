"""Reference solution — INTERNAL ONLY, NEVER EXPOSE TO USERS"""

def train_and_predict(X_train, y_train, X_test):
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model.fit(X_train, y_train)
    return model.predict(X_test)
