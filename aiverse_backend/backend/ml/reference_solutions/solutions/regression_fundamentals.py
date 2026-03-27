"""Reference solution — INTERNAL ONLY, NEVER EXPOSE TO USERS"""

def train_and_predict(X_train, y_train, X_test):
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model.predict(X_test)
