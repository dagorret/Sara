from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Dict, Iterable, Optional

from sara.core.models import Dataset, DatasetVersion, Operation


class DatasetRepository:
    """Placeholder repository; replace with Postgres implementation."""

    def __init__(self) -> None:
        self._datasets: Dict[str, Dataset] = {}
        self._versions: Dict[str, DatasetVersion] = {}
        self._operations: Dict[str, Operation] = {}

    def create_dataset(self, dataset_id: str, name: str, description: str | None = None) -> Dataset:
        if dataset_id in self._datasets:
            raise ValueError(f"Dataset '{dataset_id}' already exists.")
        dataset = Dataset(dataset_id=dataset_id, name=name, description=description, created_at=datetime.utcnow())
        self._datasets[dataset_id] = dataset
        return dataset

    def list_datasets(self) -> Iterable[Dataset]:
        return self._datasets.values()

    def get_dataset(self, dataset_id: str) -> Dataset:
        if dataset_id not in self._datasets:
            raise KeyError(f"Dataset '{dataset_id}' not found.")
        return self._datasets[dataset_id]

    def add_version(self, dataset_version: DatasetVersion) -> DatasetVersion:
        key = f"{dataset_version.dataset_id}:{dataset_version.version}"
        if key in self._versions:
            raise ValueError(f"Version '{key}' already exists.")
        self._versions[key] = dataset_version
        return dataset_version

    def get_version(self, dataset_id: str, version: str) -> DatasetVersion:
        key = f"{dataset_id}:{version}"
        if key not in self._versions:
            raise KeyError(f"Version '{key}' not found.")
        return self._versions[key]

    def create_operation(self, operation_id: str, kind: str, params: Dict[str, str]) -> Operation:
        if operation_id in self._operations:
            raise ValueError(f"Operation '{operation_id}' already exists.")
        op = Operation(operation_id=operation_id, kind=kind, params=params, created_at=datetime.utcnow())
        self._operations[operation_id] = op
        return op

    def as_debug_dict(self) -> Dict[str, Dict[str, dict]]:
        """Helper for debug endpoints (non-persistent)."""
        return {
            "datasets": {k: asdict(v) for k, v in self._datasets.items()},
            "versions": {k: asdict(v) for k, v in self._versions.items()},
            "operations": {k: asdict(v) for k, v in self._operations.items()},
        }
