from __future__ import annotations

from pathlib import Path

from .database import DuckDBManager
from .dataset import Dataset


def load_dataset(path: str, table_name: str | None = None) -> Dataset:
    csv_path = Path(path).resolve()
    manager = DuckDBManager()
    resolved_table = table_name or csv_path.stem or "data"
    table_name = manager.load_csv(str(csv_path), table_name=resolved_table)
    return Dataset(connection=manager.connection, base_table=table_name, path=str(csv_path))


def load_existing_dataset(table_name: str, path: str = "") -> Dataset:
    manager = DuckDBManager()
    return Dataset(connection=manager.connection, base_table=table_name, path=path)


def list_datasets() -> list[str]:
    manager = DuckDBManager()
    return manager.list_tables()


def cargar_csv(path: str) -> Dataset:
    return load_dataset(path)


def load_csv(path: str) -> Dataset:
    return load_dataset(path)
