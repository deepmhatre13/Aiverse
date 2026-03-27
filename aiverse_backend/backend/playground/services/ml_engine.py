import random
import time
import traceback

import numpy as np
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from sklearn.metrics import log_loss, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from playground.models import Experiment, TrainingLog
from playground.services.dataset_loader import load_dataset_arrays


ALLOWED_MODELS = {
    "logistic_regression",
    "random_forest",
    "svm",
    "knn",
    "simple_nn",
}


def _enforce_epoch_limits(hyper: dict) -> int:
    epochs = int(hyper.get("epochs") or 50)
    return max(1, min(epochs, 500))


def _sleep_per_epoch(hyper: dict) -> float:
    # UI requires visible streaming; keep within 0.3-0.5s
    return float(hyper.get("epoch_delay") or random.uniform(0.3, 0.5))


def _make_model(model_type: str, hyper: dict):
    if model_type == "logistic_regression":
        max_iter = max(50, int(hyper.get("epochs") or 200))
        C = float(hyper.get("C") or 1.0)
        return LogisticRegression(max_iter=max_iter, C=C, solver="lbfgs")
    if model_type == "random_forest":
        n_estimators = int(hyper.get("n_estimators") or 100)
        max_depth = hyper.get("max_depth")
        max_depth = int(max_depth) if max_depth not in (None, "", "null") else None
        return RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    if model_type == "svm":
        C = float(hyper.get("C") or 1.0)
        gamma = hyper.get("gamma") or "scale"
        return SVC(C=C, gamma=gamma, probability=True)
    if model_type == "knn":
        k = int(hyper.get("k") or hyper.get("n_neighbors") or 5)
        return KNeighborsClassifier(n_neighbors=max(1, k))
    if model_type == "simple_nn":
        # Prefer PyTorch if installed; otherwise fall back to sklearn-like behavior
        try:
            import torch  # noqa: F401
            return "pytorch"
        except Exception:
            return "no_torch"
    raise ValueError("Unsupported model_type")


def _broadcast_epoch(experiment_id: int, epoch: int, loss: float, accuracy: float):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"playground_{experiment_id}",
        {
            "type": "training_update",
            "data": {"epoch": epoch, "loss": loss, "accuracy": accuracy},
        },
    )


def run_training(experiment_id: int):
    exp = Experiment.objects.select_related("dataset").get(id=experiment_id)
    if exp.model_type not in ALLOWED_MODELS:
        raise ValueError("Invalid model_type")

    try:
        X, y = load_dataset_arrays(exp.dataset.name)
        X = np.array(X)
        y = np.array(y)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        hyper = exp.hyperparameters or {}
        epochs = _enforce_epoch_limits(hyper)
        delay = _sleep_per_epoch(hyper)

        # clear previous logs
        TrainingLog.objects.filter(experiment=exp).delete()

        model = _make_model(exp.model_type, hyper)

        start = time.time()

        if model == "pytorch":
            # Minimal PyTorch MLP for classification
            import torch
            import torch.nn as nn
            import torch.optim as optim

            Xtr = torch.tensor(X_train, dtype=torch.float32)
            ytr = torch.tensor(y_train, dtype=torch.long)
            Xte = torch.tensor(X_test, dtype=torch.float32)
            yte = torch.tensor(y_test, dtype=torch.long)

            n_in = Xtr.shape[1]
            n_out = int(np.max(y) + 1)
            hidden = int(hyper.get("hidden_units") or 64)
            lr = float(hyper.get("learning_rate") or 0.01)

            net = nn.Sequential(
                nn.Linear(n_in, hidden),
                nn.ReLU(),
                nn.Linear(hidden, n_out),
            )
            criterion = nn.CrossEntropyLoss()
            opt = optim.Adam(net.parameters(), lr=lr)

            for epoch in range(1, epochs + 1):
                net.train()
                opt.zero_grad()
                logits = net(Xtr)
                loss_val = criterion(logits, ytr)
                loss_val.backward()
                opt.step()

                net.eval()
                with torch.no_grad():
                    pred = net(Xte).argmax(dim=1)
                acc = float((pred == yte).float().mean().item())
                loss_float = float(loss_val.item())

                TrainingLog.objects.create(
                    experiment=exp, epoch=epoch, loss=loss_float, accuracy=acc
                )
                _broadcast_epoch(exp.id, epoch, loss_float, acc)
                time.sleep(delay)

            final_loss = float(loss_float)
            final_acc = float(acc)

        elif model == "no_torch":
            raise RuntimeError("PyTorch not installed for simple_nn")
        else:
            # sklearn models: simulate epochs by training on increasing data fraction
            n = len(X_train)
            for epoch in range(1, epochs + 1):
                frac = max(0.1, epoch / epochs)
                m = int(n * frac)
                Xi = X_train[:m]
                yi = y_train[:m]

                model.fit(Xi, yi)
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(X_test)
                    loss_val = float(log_loss(y_test, proba))
                else:
                    # SVC without proba shouldn't happen (we set probability=True)
                    pred = model.predict(X_test)
                    loss_val = float(max(0.0, 1.0 - accuracy_score(y_test, pred)))

                pred = model.predict(X_test)
                acc = float(accuracy_score(y_test, pred))

                TrainingLog.objects.create(
                    experiment=exp, epoch=epoch, loss=loss_val, accuracy=acc
                )
                _broadcast_epoch(exp.id, epoch, loss_val, acc)
                time.sleep(delay)

            final_loss = float(loss_val)
            final_acc = float(acc)

        training_time = float(time.time() - start)
        metrics = {"accuracy": final_acc, "loss": final_loss, "training_time": training_time}

        with transaction.atomic():
            exp.status = Experiment.STATUS_COMPLETED
            exp.metrics = metrics
            exp.error = None
            exp.save(update_fields=["status", "metrics", "error", "updated_at"])

        return metrics

    except Exception:
        tb = traceback.format_exc()
        with transaction.atomic():
            exp.status = Experiment.STATUS_FAILED
            exp.error = tb
            exp.logs = (exp.logs or []) + [{"type": "error", "traceback": tb}]
            exp.save(update_fields=["status", "error", "logs", "updated_at"])
        raise

import traceback

import pandas as pd
from django.db import transaction
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from playground.models import Experiment


CLASSIFICATION_MODELS = {
    'logistic_regression': LogisticRegression,
    'random_forest': RandomForestClassifier,
}

REGRESSION_MODELS = {
    'linear_regression': LinearRegression,
    'random_forest': RandomForestRegressor,
}


class MLExecutionError(Exception):
    pass


def _build_model(experiment: Experiment):
    hyper = experiment.hyperparameters or {}

    if experiment.task_type == Experiment.TASK_CLASSIFICATION:
        if experiment.model_type not in CLASSIFICATION_MODELS:
            raise MLExecutionError('Unsupported classification model_type')
        if experiment.model_type == 'logistic_regression':
            # sklearn LogisticRegression doesn't accept learning_rate directly,
            # so we map UI hyperparameters to parameters that affect training.
            learning_rate = hyper.get('learning_rate', None)
            epochs = hyper.get('epochs', None)
            max_iter = int(epochs) if epochs not in (None, '') else int(hyper.get('max_iter', 200))

            # Map "learning_rate" slider to regularization strength C.
            # Higher learning_rate -> stronger regularization (smaller C).
            C = 1.0
            if learning_rate not in (None, ''):
                try:
                    lr = float(learning_rate)
                    lr = max(lr, 1e-8)
                    C = 1.0 / lr
                    C = max(1e-4, min(C, 1e4))
                except Exception:
                    C = 1.0

            kwargs = {
                'max_iter': max_iter,
                'C': float(C),
                'random_state': 42,
                'solver': 'lbfgs',
            }
            return LogisticRegression(**kwargs)
        kwargs = {
            # If UI doesn't send n_estimators/max_depth, we still want `epochs`
            # to affect the model in a meaningful way.
            'n_estimators': int(hyper.get('n_estimators', hyper.get('epochs', 100))),
            'max_depth': int(hyper['max_depth']) if hyper.get('max_depth') not in (None, '') else None,
            'random_state': 42,
        }
        return RandomForestClassifier(**kwargs)

    if experiment.task_type == Experiment.TASK_REGRESSION:
        if experiment.model_type not in REGRESSION_MODELS:
            raise MLExecutionError('Unsupported regression model_type')
        if experiment.model_type == 'linear_regression':
            return LinearRegression()
        kwargs = {
            'n_estimators': int(hyper.get('n_estimators', hyper.get('epochs', 100))),
            'max_depth': int(hyper['max_depth']) if hyper.get('max_depth') not in (None, '') else None,
            'random_state': 42,
        }
        return RandomForestRegressor(**kwargs)

    raise MLExecutionError('task_type is not configured for experiment')


def run_experiment(experiment_id: int):
    """Load dataset, preprocess, train, evaluate, and persist experiment results."""
    exp = Experiment.objects.select_related('dataset').get(pk=experiment_id)

    try:
        dataset = exp.dataset
        if not dataset.file:
            raise MLExecutionError('Dataset file is missing')
        if not dataset.target_column:
            raise MLExecutionError('target_column is required before training')

        df = pd.read_csv(dataset.file.path)
        if df.empty:
            raise MLExecutionError('Dataset is empty')
        if dataset.target_column not in df.columns:
            raise MLExecutionError('target_column not found in dataset columns')

        y = df[dataset.target_column]
        X = df.drop(columns=[dataset.target_column])
        if X.shape[1] == 0:
            raise MLExecutionError('Dataset must have at least one feature column')

        numeric_cols = X.select_dtypes(include=['number', 'bool']).columns.tolist()
        categorical_cols = [c for c in X.columns if c not in numeric_cols]

        preprocess = ColumnTransformer(
            transformers=[
                (
                    'num',
                    Pipeline(steps=[('imputer', SimpleImputer(strategy='median'))]),
                    numeric_cols,
                ),
                (
                    'cat',
                    Pipeline(
                        steps=[
                            ('imputer', SimpleImputer(strategy='most_frequent')),
                            ('onehot', OneHotEncoder(handle_unknown='ignore')),
                        ]
                    ),
                    categorical_cols,
                ),
            ]
        )

        model = _build_model(exp)
        pipeline = Pipeline(steps=[('preprocess', preprocess), ('model', model)])

        stratify = y if exp.task_type == Experiment.TASK_CLASSIFICATION else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=stratify,
        )

        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        if exp.task_type == Experiment.TASK_CLASSIFICATION:
            acc = float(accuracy_score(y_test, preds))
            f1 = float(f1_score(y_test, preds, average='weighted', zero_division=0))
            metrics = {
                'accuracy': acc,
                'f1_score': f1,
                'loss': float(max(0.0, 1.0 - acc)),
                'history': [{'epoch': 1, 'accuracy': acc, 'loss': float(max(0.0, 1.0 - acc))}],
            }
            score = acc
        else:
            rmse = float(mean_squared_error(y_test, preds, squared=False))
            r2 = float(r2_score(y_test, preds))
            metrics = {
                'rmse': rmse,
                'r2_score': r2,
                'loss': rmse,
                'history': [{'epoch': 1, 'accuracy': max(0.0, min(1.0, r2)), 'loss': rmse}],
            }
            score = r2

        with transaction.atomic():
            exp.status = Experiment.STATUS_SUCCESS
            exp.score = score
            exp.metrics = metrics
            exp.error = None
            exp.save(update_fields=['status', 'score', 'metrics', 'error', 'updated_at'])

        return {'score': score, 'metrics': metrics}

    except Exception:
        with transaction.atomic():
            exp.status = Experiment.STATUS_FAILED
            exp.error = traceback.format_exc()
            exp.save(update_fields=['status', 'error', 'updated_at'])
        raise
