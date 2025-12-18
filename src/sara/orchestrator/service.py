from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from sara.core import Dataset, DatasetVersion
from sara.engine import DuckDBEngine
from sara.storage import DatasetRepository


class Orchestrator:
    """Coordinates storage + engine for CLI/API consumers."""

    def __init__(self, repository: DatasetRepository | None = None, engine: DuckDBEngine | None = None) -> None:
        self.repository = repository or DatasetRepository()
        self.engine = engine or DuckDBEngine()

    # Dataset operations
    def create_dataset(self, dataset_id: str, name: str, description: str | None = None) -> Dataset:
        return self.repository.create_dataset(dataset_id=dataset_id, name=name, description=description)

    def list_datasets(self) -> list[Dataset]:
        return list(self.repository.list_datasets())

    def get_dataset(self, dataset_id: str) -> Dataset:
        return self.repository.get_dataset(dataset_id)

    # Import
    def import_csv(self, dataset_id: str, csv_path: Path, version: str = "v1") -> DatasetVersion:
        _ = self.repository.get_dataset(dataset_id)  # ensure exists
        out_path = self.engine.import_csv(dataset_id=dataset_id, csv_path=csv_path, version=version)
        version_obj = DatasetVersion(dataset_id=dataset_id, version=version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    def import_xlsx(self, dataset_id: str, xlsx_path: Path, sheet: str | None, version: str = "v1") -> DatasetVersion:
        _ = self.repository.get_dataset(dataset_id)
        out_path = self.engine.import_xlsx(dataset_id=dataset_id, xlsx_path=xlsx_path, sheet=sheet, version=version)
        version_obj = DatasetVersion(dataset_id=dataset_id, version=version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    # Preview / profile
    def preview(self, dataset_version: DatasetVersion, limit: int = 100):
        return self.engine.preview(Path(dataset_version.path), limit=limit)

    def profile(self, dataset_version: DatasetVersion):
        return self.engine.profile(Path(dataset_version.path))

    # Transformations (stubs)
    def filter(
        self,
        dataset_version: DatasetVersion,
        where: str,
        out_version: str,
    ) -> DatasetVersion:
        out_path = self.engine.filter(Path(dataset_version.path), where=where, out_version_path=self._version_path(dataset_version.dataset_id, out_version))
        version_obj = DatasetVersion(dataset_id=dataset_version.dataset_id, version=out_version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    def winsorize(
        self,
        dataset_version: DatasetVersion,
        column: str,
        p_low: float,
        p_high: float,
        out_column: str | None,
        out_version: str,
    ) -> DatasetVersion:
        out_path = self.engine.winsorize(
            Path(dataset_version.path),
            column=column,
            p_low=p_low,
            p_high=p_high,
            out_column=out_column,
            out_version_path=self._version_path(dataset_version.dataset_id, out_version),
        )
        version_obj = DatasetVersion(dataset_id=dataset_version.dataset_id, version=out_version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    def recode(
        self,
        dataset_version: DatasetVersion,
        column: str,
        mapping: Dict[str, Any],
        out_column: str | None,
        out_version: str,
    ) -> DatasetVersion:
        out_path = self.engine.recode(
            Path(dataset_version.path),
            column=column,
            mapping=mapping,
            out_column=out_column,
            out_version_path=self._version_path(dataset_version.dataset_id, out_version),
        )
        version_obj = DatasetVersion(dataset_id=dataset_version.dataset_id, version=out_version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    # Stats
    def mean(self, dataset_version: DatasetVersion, column: str, where: str | None = None) -> float:
        return self.engine.mean(Path(dataset_version.path), column=column, where=where)

    def _version_path(self, dataset_id: str, version: str) -> Path:
        # This will likely become a configurable storage layout
        return Path(self.engine.base_dir) / "datasets" / dataset_id / version / "data.parquet"
