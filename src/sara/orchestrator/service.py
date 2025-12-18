from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from sara.config.settings import SARASettings
from sara.core import Dataset, DatasetVersion
from sara.engine.duckdb_engine import DuckDBEngine
from sara.storage.layout import StorageLayout
from sara.storage.repository import DatasetRepository


class Orchestrator:
    """
    Coordina storage + engine para consumidores (CLI/API).

    Cambios clave:
      - ya NO construye paths (eso lo hace StorageLayout)
      - expone get_version para que el CLI no toque repository directamente
      - usa settings para inicializar defaults coherentes
    """

    def __init__(
        self,
        repository: DatasetRepository | None = None,
        engine: DuckDBEngine | None = None,
        layout: StorageLayout | None = None,
        settings: SARASettings | None = None,
    ) -> None:
        # Settings primero: define defaults
        self.settings = settings or SARASettings()

        # Layout: dueño del filesystem layout
        self.layout = layout or StorageLayout(data_dir=self.settings.data_dir)

        # Repository (por ahora in-memory)
        self.repository = repository or DatasetRepository()

        # Engine: usa settings para DB duckdb (en memoria o archivo)
        self.engine = engine or DuckDBEngine(database=self.settings.duckdb_database)

    # ---------------------------
    # Dataset ops
    # ---------------------------

    def create_dataset(self, dataset_id: str, name: str, description: str | None = None) -> Dataset:
        return self.repository.create_dataset(dataset_id=dataset_id, name=name, description=description)

    def list_datasets(self) -> list[Dataset]:
        return list(self.repository.list_datasets())

    def get_dataset(self, dataset_id: str) -> Dataset:
        return self.repository.get_dataset(dataset_id)

    # ---------------------------
    # Version ops (nuevo: encapsula acceso a repository)
    # ---------------------------

    def get_version(self, dataset_id: str, version: str) -> DatasetVersion:
        """
        Nuevo método para que CLI/API no acceda a `orc.repository` directamente.

        Esto es importante porque:
          - te permite reemplazar DatasetRepository (memory) por Postgres sin
            modificar el CLI.
        """
        return self.repository.get_version(dataset_id, version)

    def list_versions(self, dataset_id: str) -> list[DatasetVersion]:
        return list(self.repository.list_versions(dataset_id))

    # ---------------------------
    # Import
    # ---------------------------

    def import_csv(self, dataset_id: str, csv_path: Path, version: str = "v1") -> DatasetVersion:
        _ = self.repository.get_dataset(dataset_id)  # asegura existencia

        out_path = self.layout.version_path(dataset_id, version)
        out_path = self.engine.import_csv(csv_path=csv_path, out_path=out_path)

        version_obj = DatasetVersion(dataset_id=dataset_id, version=version, path=str(out_path))

        # Registro en repo: si falla, intentamos rollback de archivo (best effort)
        try:
            self.repository.add_version(version_obj)
        except Exception:
            # Best-effort cleanup. Si falla el unlink, no ocultamos el error original.
            try:
                out_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        return version_obj

    def import_xlsx(self, dataset_id: str, xlsx_path: Path, sheet: str | None, version: str = "v1") -> DatasetVersion:
        _ = self.repository.get_dataset(dataset_id)

        out_path = self.layout.version_path(dataset_id, version)
        out_path = self.engine.import_xlsx(xlsx_path=xlsx_path, out_path=out_path, sheet=sheet)

        version_obj = DatasetVersion(dataset_id=dataset_id, version=version, path=str(out_path))
        try:
            self.repository.add_version(version_obj)
        except Exception:
            try:
                out_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

        return version_obj

    # ---------------------------
    # Preview / profile
    # ---------------------------

    def preview(self, dataset_version: DatasetVersion, limit: int = 100):
        return self.engine.preview(Path(dataset_version.path), limit=limit)

    def profile(self, dataset_version: DatasetVersion):
        return self.engine.profile(Path(dataset_version.path))

    # ---------------------------
    # Transformaciones
    # ---------------------------

    def filter(self, dataset_version: DatasetVersion, where: str, out_version: str) -> DatasetVersion:
        out_path = self.layout.version_path(dataset_version.dataset_id, out_version)

        out_path = self.engine.filter(
            Path(dataset_version.path),
            where=where,
            out_version_path=out_path,
        )
        version_obj = DatasetVersion(dataset_id=dataset_version.dataset_id, version=out_version, path=str(out_path))

        try:
            self.repository.add_version(version_obj)
        except Exception:
            try:
                out_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise

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
        out_path = self.layout.version_path(dataset_version.dataset_id, out_version)

        out_path = self.engine.winsorize(
            Path(dataset_version.path),
            column=column,
            p_low=p_low,
            p_high=p_high,
            out_column=out_column,
            out_version_path=out_path,
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
        out_path = self.layout.version_path(dataset_version.dataset_id, out_version)

        out_path = self.engine.recode(
            Path(dataset_version.path),
            column=column,
            mapping=mapping,
            out_column=out_column,
            out_version_path=out_path,
        )
        version_obj = DatasetVersion(dataset_id=dataset_version.dataset_id, version=out_version, path=str(out_path))
        self.repository.add_version(version_obj)
        return version_obj

    # ---------------------------
    # Stats
    # ---------------------------

    def mean(self, dataset_version: DatasetVersion, column: str, where: str | None = None) -> float:
        return self.engine.mean(Path(dataset_version.path), column=column, where=where)