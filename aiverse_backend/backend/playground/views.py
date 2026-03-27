from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from playground.models import Dataset, Experiment, TrainingLog
from playground.serializers import (
    DatasetSerializer,
    ExperimentDetailSerializer,
    ExperimentSelectModelSerializer,
    ExperimentSetHyperparametersSerializer,
    ExperimentStartSerializer,
)
from playground.services.dataset_loader import ensure_preloaded_datasets
from playground.tasks import run_training_task


ALLOWED_MODELS = {"logistic_regression", "random_forest", "svm", "knn", "simple_nn"}
MAX_CONCURRENT_RUNNING = 2


def envelope(success: bool, data=None, error=None, http_status=status.HTTP_200_OK):
    return Response({'success': success, 'data': data or {}, 'error': error}, status=http_status)


def _ensure_auth(request):
    if not request.user or not request.user.is_authenticated:
        return envelope(False, error='authentication required', http_status=status.HTTP_401_UNAUTHORIZED)
    return None


def _experiment_for_user(user, experiment_id: int):
    return Experiment.objects.select_related('dataset').filter(pk=experiment_id, user=user).first()


def _compat_job_payload(exp: Experiment):
    # Current frontend expects these keys
    metrics = exp.metrics or {}
    logs = list(exp.training_logs.all().order_by("epoch").values("epoch", "loss", "accuracy")[:500])
    return {
        "id": exp.id,
        "status": "training" if exp.status == Experiment.STATUS_RUNNING else "completed" if exp.status == Experiment.STATUS_COMPLETED else "failed" if exp.status == Experiment.STATUS_FAILED else "created",
        "dataset_type": str(exp.dataset_id),
        "model_type": exp.model_type,
        "learning_rate": (exp.hyperparameters or {}).get("learning_rate"),
        "epochs": (exp.hyperparameters or {}).get("epochs"),
        "batch_size": (exp.hyperparameters or {}).get("batch_size"),
        "hidden_units": (exp.hyperparameters or {}).get("hidden_units"),
        "final_accuracy": metrics.get("accuracy"),
        "final_loss": metrics.get("loss"),
        "error_message": exp.error,
        "created_at": exp.created_at.isoformat(),
        "updated_at": exp.updated_at.isoformat(),
        "metrics": logs,
    }

class DatasetListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        ensure_preloaded_datasets()
        datasets = Dataset.objects.all().order_by("name")
        return envelope(True, DatasetSerializer(datasets, many=True).data)


class ExperimentStartView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        ensure_preloaded_datasets()
        serializer = ExperimentStartSerializer(data=request.data)
        if not serializer.is_valid():
            return envelope(False, error=str(serializer.errors), http_status=status.HTTP_400_BAD_REQUEST)

        dataset = Dataset.objects.filter(id=serializer.validated_data["dataset_id"]).first()
        if not dataset:
            return envelope(False, error="dataset not found", http_status=status.HTTP_404_NOT_FOUND)

        running = Experiment.objects.filter(user=request.user, status=Experiment.STATUS_RUNNING).count()
        if running >= MAX_CONCURRENT_RUNNING:
            return envelope(False, error="too many concurrent running experiments", http_status=status.HTTP_429_TOO_MANY_REQUESTS)

        exp = Experiment.objects.create(user=request.user, dataset=dataset, current_step=1, status=Experiment.STATUS_CREATED)
        return envelope(True, {"experiment_id": exp.id, "current_step": exp.current_step}, http_status=status.HTTP_201_CREATED)


class ExperimentSelectModelView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        if exp.current_step != 1:
            return envelope(False, error='cannot skip steps: model selection requires current_step=1', http_status=status.HTTP_400_BAD_REQUEST)

        serializer = ExperimentSelectModelSerializer(data=request.data)
        if not serializer.is_valid():
            return envelope(False, error=str(serializer.errors), http_status=status.HTTP_400_BAD_REQUEST)

        model_type = serializer.validated_data["model_type"]
        if model_type not in ALLOWED_MODELS:
            return envelope(False, error="invalid model_type", http_status=status.HTTP_400_BAD_REQUEST)

        exp.model_type = model_type
        exp.current_step = 2
        exp.status = Experiment.STATUS_READY
        exp.save(update_fields=['model_type', 'current_step', 'status', 'updated_at'])
        return envelope(True, {'experiment_id': exp.id, 'current_step': exp.current_step})


class ExperimentSetHyperparametersView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        if exp.current_step != 2:
            return envelope(False, error='cannot skip steps: hyperparameters require current_step=2', http_status=status.HTTP_400_BAD_REQUEST)

        serializer = ExperimentSetHyperparametersSerializer(data=request.data)
        if not serializer.is_valid():
            return envelope(False, error=str(serializer.errors), http_status=status.HTTP_400_BAD_REQUEST)

        hyper = serializer.validated_data
        epochs = int(hyper.get("epochs") or 50)
        if epochs > 500:
            return envelope(False, error="epochs must be <= 500", http_status=status.HTTP_400_BAD_REQUEST)
        exp.hyperparameters = hyper
        exp.current_step = 3
        exp.status = Experiment.STATUS_READY
        exp.save(update_fields=['hyperparameters', 'current_step', 'status', 'updated_at'])
        return envelope(True, {'experiment_id': exp.id, 'current_step': exp.current_step})


class ExperimentTrainView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'playground_train'

    def post(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)

        if exp.current_step != 3:
            return envelope(False, error='cannot train before step 3 is complete', http_status=status.HTTP_400_BAD_REQUEST)
        if not exp.model_type:
            return envelope(False, error="model must be selected before training", http_status=status.HTTP_400_BAD_REQUEST)
        if not exp.hyperparameters:
            return envelope(False, error="hyperparameters required before training", http_status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            exp.current_step = 4
            exp.status = Experiment.STATUS_RUNNING
            exp.error = None
            exp.metrics = {}
            exp.logs = []
            exp.save(update_fields=['current_step', 'status', 'error', 'metrics', 'logs', 'updated_at'])

        task = run_training_task.delay(exp.id)
        data = {'experiment_id': exp.id, 'current_step': exp.current_step, 'status': exp.status, 'task_id': task.id}
        return envelope(True, data, http_status=status.HTTP_202_ACCEPTED)


class ExperimentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        payload = ExperimentDetailSerializer(exp).data
        return envelope(True, payload)


class PlaygroundCompatOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        ensure_preloaded_datasets()
        datasets = Dataset.objects.all().order_by("name")
        ds_payload = [
            {
                "id": d.id,
                "name": d.name.replace("_", " ").title(),
                "description": d.description,
                "task_type": d.task_type,
                "num_features": d.n_features,
                "num_samples": d.n_samples,
            }
            for d in datasets
        ]

        models = [
            {"id": "logistic_regression", "name": "Logistic Regression", "description": "Linear classifier.", "hyperparameters": {"learning_rate": True, "epochs": True}},
            {"id": "random_forest", "name": "Random Forest", "description": "Tree ensemble classifier.", "hyperparameters": {"n_estimators": True, "max_depth": True, "epochs": True}},
            {"id": "svm", "name": "Support Vector Machine (SVM)", "description": "Margin-based classifier.", "hyperparameters": {"epochs": True}},
            {"id": "knn", "name": "K-Nearest Neighbors (KNN)", "description": "Instance-based classifier.", "hyperparameters": {"epochs": True}},
            {"id": "simple_nn", "name": "Simple Neural Network", "description": "Tiny MLP (PyTorch).", "hyperparameters": {"learning_rate": True, "epochs": True, "hidden_units": True, "batch_size": True}},
        ]

        compatibility = {str(d["id"]): [m["id"] for m in models] for d in ds_payload}
        return envelope(True, {"datasets": ds_payload, "models": models, "compatibility": compatibility})


class PlaygroundCompatJobsView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'playground_jobs'

    def get(self, request):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        jobs = Experiment.objects.filter(user=request.user).select_related('dataset').order_by('-created_at')
        return envelope(True, [_compat_job_payload(exp) for exp in jobs])

    def post(self, request):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        dataset_id = request.data.get("dataset_type") or request.data.get("dataset_id")
        model_type = request.data.get("model_type")

        if not dataset_id or not model_type:
            return envelope(False, error='dataset_type and model_type are required', http_status=status.HTTP_400_BAD_REQUEST)

        ensure_preloaded_datasets()
        dataset = Dataset.objects.filter(pk=dataset_id).first()
        if not dataset:
            return envelope(False, error='dataset not found', http_status=status.HTTP_404_NOT_FOUND)

        if model_type not in ALLOWED_MODELS:
            return envelope(False, error="invalid model_type", http_status=status.HTTP_400_BAD_REQUEST)

        hyper = {
            'learning_rate': request.data.get('learning_rate'),
            'epochs': request.data.get('epochs'),
            'batch_size': request.data.get('batch_size'),
            'hidden_units': request.data.get('hidden_units'),
            'n_estimators': request.data.get('n_estimators'),
            'max_depth': request.data.get('max_depth'),
        }
        hyper = {k: v for k, v in hyper.items() if v not in (None, '')}

        # Create and advance through state machine
        with transaction.atomic():
            exp = Experiment.objects.create(user=request.user, dataset=dataset, current_step=1, status=Experiment.STATUS_CREATED)
            exp.model_type = model_type
            exp.current_step = 2
            exp.status = Experiment.STATUS_READY
            exp.save(update_fields=["model_type", "current_step", "status", "updated_at"])

            if not hyper:
                return envelope(False, error="hyperparameters required", http_status=status.HTTP_400_BAD_REQUEST)
            epochs = int(hyper.get("epochs") or 50)
            if epochs > 500:
                return envelope(False, error="epochs must be <= 500", http_status=status.HTTP_400_BAD_REQUEST)
            exp.hyperparameters = hyper
            exp.current_step = 3
            exp.save(update_fields=["hyperparameters", "current_step", "updated_at"])

            exp.current_step = 4
            exp.status = Experiment.STATUS_RUNNING
            exp.metrics = {}
            exp.logs = []
            exp.error = None
            exp.save(update_fields=["current_step", "status", "metrics", "logs", "error", "updated_at"])

        # Non-blocking: enqueue Celery job
        task = run_training_task.delay(exp.id)
        payload = _compat_job_payload(exp)
        payload["task_id"] = task.id
        return envelope(True, payload, http_status=status.HTTP_201_CREATED)


class PlaygroundCompatJobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        return envelope(True, _compat_job_payload(exp))


class PlaygroundCompatJobStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        return envelope(True, _compat_job_payload(exp))


class PlaygroundCompatJobMetricsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, experiment_id: int):
        auth_error = _ensure_auth(request)
        if auth_error:
            return auth_error
        exp = _experiment_for_user(request.user, experiment_id)
        if not exp:
            return envelope(False, error='experiment not found', http_status=status.HTTP_404_NOT_FOUND)
        rows = list(exp.training_logs.all().order_by("epoch").values("epoch", "loss", "accuracy")[:500])
        return envelope(True, rows)
