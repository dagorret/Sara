from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StorageLayout:
    """
    Dueño ÚNICO del layout de archivos en disco.

    Este es el punto clave de tu pregunta:
      - El Orchestrator NO debe inventar paths.
      - El Engine NO debería decidir "dónde" se guarda cada versión.
      - Ambos deberían pedirle al Layout el path final (o recibirlo ya resuelto).

    Ventaja:
      - Si mañana cambiás layout (por ejemplo particionar por fecha,
        o guardar en S3, o usar hash), tocás SOLO esta capa.
    """

    data_dir: Path

    def version_dir(self, dataset_id: str, version: str) -> Path:
        """
        Directorio para una versión.

        Ej: data/datasets/hogares_2023/v1/
        """
        return self.data_dir / "datasets" / dataset_id / version

    def version_path(self, dataset_id: str, version: str) -> Path:
        """
        Path del parquet principal de la versión.

        Ej: data/datasets/hogares_2023/v1/data.parquet
        """
        return self.version_dir(dataset_id, version) / "data.parquet"