from __future__ import annotations

import logging
from pathlib import Path

from .database import DuckDBManager
from .dataset import Dataset
from .exceptions import QueryError, ValidationError


log = logging.getLogger(__name__)


def load_dataset(path: str, table_name: str | None = None) -> Dataset:
    csv_path = Path(path).resolve()
    if not csv_path.exists():
        raise ValidationError(f"El archivo no existe: {csv_path}")
    if not csv_path.is_file():
        raise ValidationError(f"La ruta no corresponde a un archivo: {csv_path}")

    manager = DuckDBManager()
    resolved_table = table_name or csv_path.stem or "data"
    try:
        table_name = manager.load_csv(str(csv_path), table_name=resolved_table)
    except Exception as exc:
        log.error("Dataset load failed for %s: %s", csv_path, exc)
        raise QueryError(f"No se pudo cargar el dataset desde '{csv_path}'.") from exc

    log.info("Dataset loaded successfully: table=%s path=%s", table_name, csv_path)
    return Dataset(connection=manager.connection, base_table=table_name, path=str(csv_path))


def load_existing_dataset(table_name: str, path: str = "") -> Dataset:
    manager = DuckDBManager()
    log.info("Loading existing dataset handle for table '%s'", table_name)
    return Dataset(connection=manager.connection, base_table=table_name, path=path)


def list_datasets() -> list[str]:
    manager = DuckDBManager()
    datasets = manager.list_tables()
    log.info("Listing datasets: %s", datasets)
    return datasets


def cargar_csv(path: str) -> Dataset:
    return load_dataset(path)


def load_csv(path: str) -> Dataset:
    return load_dataset(path)
