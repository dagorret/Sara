from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SARASettings:
    """
    Configuración central de la app.

    La idea es que:
      - CLI/API cargue settings (por defecto o por ENV/archivo en el futuro)
      - una "factory" arme Orchestrator con repo/engine/layout adecuados

    IMPORTANTE (diseño):
      - settings NO define el layout exacto de archivos (eso es StorageLayout)
      - settings SÍ define el root/base (data_dir) donde vive el storage local
      - settings también define backends (memory/postgres, duckdb, etc.)

    Por ahora mantenemos todo simple y sin dependencias (sin Pydantic).
    """

    # Root para archivos locales (parquets, outputs, etc.)
    data_dir: Path = Path("data")

    # DuckDB: si querés persistir el catálogo/estado (opcional)
    # - ":memory:" = efímero
    # - "data/sara.duckdb" = persistente
    duckdb_database: str = ":memory:"

    # Postgres (futuro): DSN o cadena de conexión.
    # Ejemplo: "postgresql://user:pass@host:5432/dbname"
    postgres_dsn: str | None = None

    # Selección de backend del repositorio:
    # - "memory": el DatasetRepository actual
    # - "postgres": futuro PostgresDatasetRepository
    repository_backend: str = "memory"

    # Selección de engine:
    # - "duckdb": el engine actual
    engine_backend: str = "duckdb"