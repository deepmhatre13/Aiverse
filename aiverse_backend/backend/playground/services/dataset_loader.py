from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple

from sklearn.datasets import load_breast_cancer, load_digits, load_iris, load_wine

from playground.models import Dataset


@dataclass(frozen=True)
class LoadedDataset:
    name: str
    description: str
    X_shape: Tuple[int, int]


def _load_meta(loader: Callable[[], object], name: str, description: str) -> LoadedDataset:
    ds = loader()
    X = getattr(ds, "data", None)
    n_samples = int(getattr(X, "shape", (0, 0))[0] or 0)
    n_features = int(getattr(X, "shape", (0, 0))[1] or 0)
    return LoadedDataset(name=name, description=description, X_shape=(n_samples, n_features))


PRELOADED_DATASETS: Dict[str, Tuple[Callable[[], object], str]] = {
    "iris": (load_iris, "Classic Iris flower classification dataset."),
    "breast_cancer": (load_breast_cancer, "Breast cancer classification dataset."),
    "wine": (load_wine, "Wine cultivar classification dataset."),
    "digits": (load_digits, "Handwritten digits classification dataset."),
}


def ensure_preloaded_datasets() -> None:
    """
    Ensure the 4 predefined datasets exist in DB.
    Safe to call multiple times.
    """
    for name, (loader, desc) in PRELOADED_DATASETS.items():
        meta = _load_meta(loader, name=name, description=desc)
        Dataset.objects.update_or_create(
            name=name,
            defaults={
                "task_type": Dataset.TASK_CLASSIFICATION,
                "description": meta.description,
                "n_samples": meta.X_shape[0],
                "n_features": meta.X_shape[1],
            },
        )


def load_dataset_arrays(dataset_name: str):
    """
    Load actual samples dynamically from sklearn.
    Returns (X, y).
    """
    if dataset_name not in PRELOADED_DATASETS:
        raise ValueError("Unsupported dataset")
    loader, _ = PRELOADED_DATASETS[dataset_name]
    ds = loader()
    return ds.data, ds.target

