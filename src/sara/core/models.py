from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Dataset:
    dataset_id: str
    name: str
    description: str | None = None
    created_at: datetime | None = None


@dataclass
class DatasetVersion:
    dataset_id: str
    version: str
    path: str
    created_at: datetime | None = None
    operation_id: str | None = None


@dataclass
class Operation:
    operation_id: str
    kind: str
    params: Dict[str, str]
    created_at: datetime | None = None


@dataclass
class Run:
    run_id: str
    dataset_version: str
    method: str
    params: Dict[str, str]
    created_at: datetime | None = None
