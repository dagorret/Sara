from __future__ import annotations

import json
import logging
from pathlib import Path
import re

import duckdb
import pandas as pd

from .config import DB_PATH


log = logging.getLogger(__name__)


def quote_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


class DuckDBManager:
    _shared_connections: dict[str, duckdb.DuckDBPyConnection] = {}

    def __init__(self, database_path: str = DB_PATH) -> None:
        self.database_path = str(Path(database_path).resolve())
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        connection = self._shared_connections.get(self.database_path)
        if connection is None:
            log.info("Opening DuckDB connection at %s", self.database_path)
            connection = duckdb.connect(database=self.database_path)
            self._shared_connections[self.database_path] = connection

        self.connection = connection
        self._ensure_analysis_state_table()
        self._ensure_analysis_version_table()

    @staticmethod
    def sanitize_table_name(name: str) -> str:
        normalized = re.sub(r"[^0-9a-zA-Z_]+", "_", name.strip().lower())
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        if not normalized:
            normalized = "data"
        if normalized[0].isdigit():
            normalized = f"dataset_{normalized}"
        return normalized

    def list_tables(self) -> list[str]:
        rows = self.connection.execute("SHOW TABLES").fetchall()
        internal_tables = {"analysis_states", "analysis_versions"}
        return [row[0] for row in rows if row[0] not in internal_tables]

    def table_exists(self, table_name: str) -> bool:
        return table_name in self.list_tables()

    def generate_table_name(self, base_name: str) -> str:
        sanitized = self.sanitize_table_name(base_name)
        if not self.table_exists(sanitized):
            return sanitized

        suffix = 2
        candidate = f"{sanitized}_{suffix}"
        while self.table_exists(candidate):
            suffix += 1
            candidate = f"{sanitized}_{suffix}"
        return candidate

    def load_csv(self, path: str, table_name: str = "data") -> str:
        csv_path = str(Path(path).resolve())
        resolved_table_name = self.generate_table_name(table_name)
        table_ref = quote_identifier(resolved_table_name)
        log.info("Loading CSV into DuckDB table '%s' from %s", resolved_table_name, csv_path)
        self.connection.execute(
            f"CREATE OR REPLACE TABLE {table_ref} AS "
            "SELECT * FROM read_csv_auto(?)",
            [csv_path],
        )
        return resolved_table_name

    def _ensure_analysis_state_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_states (
                id BIGINT PRIMARY KEY,
                name TEXT,
                dataset TEXT,
                filters TEXT,
                order_by TEXT,
                selected_columns TEXT,
                model_type TEXT,
                y TEXT,
                x TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.execute(
            "ALTER TABLE analysis_states ADD COLUMN IF NOT EXISTS model_type TEXT"
        )

    def _ensure_analysis_version_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_versions (
                id BIGINT PRIMARY KEY,
                analysis_name TEXT,
                version INTEGER,
                parent_version INTEGER,
                branch TEXT,
                dataset TEXT,
                filters TEXT,
                order_by TEXT,
                selected_columns TEXT,
                model_type TEXT,
                y TEXT,
                x TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.execute(
            "ALTER TABLE analysis_versions ADD COLUMN IF NOT EXISTS model_type TEXT"
        )
        self.connection.execute(
            "ALTER TABLE analysis_versions ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT 'main'"
        )

    def list_analysis_states(self) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT id, name, dataset, filters, order_by, selected_columns, model_type, y, x, created_at
            FROM analysis_states
            ORDER BY created_at DESC, id DESC
            """
        ).fetchall()
        return [
            {
                "id": row[0],
                "name": row[1],
                "dataset": row[2],
                "filters": json.loads(row[3]) if row[3] else [],
                "order_by": json.loads(row[4]) if row[4] else None,
                "selected_columns": json.loads(row[5]) if row[5] else None,
                "model_type": row[6],
                "y": row[7],
                "x": json.loads(row[8]) if row[8] else [],
                "created_at": row[9],
            }
            for row in rows
        ]

    def save_analysis_state(
        self,
        *,
        name: str,
        dataset: str,
        filters: list[str],
        order_by: dict | None,
        selected_columns: list[str] | None,
        model_type: str | None,
        y: str | None,
        x: list[str],
    ) -> int:
        next_id = self.connection.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM analysis_states"
        ).fetchone()[0]
        self.connection.execute(
            """
            INSERT INTO analysis_states (
                id, name, dataset, filters, order_by, selected_columns, model_type, y, x
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                int(next_id),
                name,
                dataset,
                json.dumps(filters),
                json.dumps(order_by) if order_by is not None else None,
                json.dumps(selected_columns) if selected_columns is not None else None,
                model_type,
                y,
                json.dumps(x),
            ],
        )
        return int(next_id)

    def get_analysis_state(self, state_id: int) -> dict | None:
        row = self.connection.execute(
            """
            SELECT id, name, dataset, filters, order_by, selected_columns, model_type, y, x, created_at
            FROM analysis_states
            WHERE id = ?
            """,
            [int(state_id)],
        ).fetchone()
        if row is None:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "dataset": row[2],
            "filters": json.loads(row[3]) if row[3] else [],
            "order_by": json.loads(row[4]) if row[4] else None,
            "selected_columns": json.loads(row[5]) if row[5] else None,
            "model_type": row[6],
            "y": row[7],
            "x": json.loads(row[8]) if row[8] else [],
            "created_at": row[9],
        }

    def list_analysis_names(self) -> list[str]:
        rows = self.connection.execute(
            """
            SELECT DISTINCT analysis_name
            FROM analysis_versions
            ORDER BY analysis_name ASC
            """
        ).fetchall()
        return [row[0] for row in rows]

    def save_analysis_version(
        self,
        *,
        analysis_name: str,
        parent_version_id: int | None = None,
        branch: str = "main",
        dataset: str,
        filters: list[str],
        order_by: dict | None,
        selected_columns: list[str] | None,
        model_type: str | None,
        y: str | None,
        x: list[str],
    ) -> dict:
        next_id = self.connection.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM analysis_versions"
        ).fetchone()[0]
        previous = self.connection.execute(
            """
            SELECT id, version
            FROM analysis_versions
            WHERE analysis_name = ?
            ORDER BY version DESC
            LIMIT 1
            """,
            [analysis_name],
        ).fetchone()
        next_version = 1 if previous is None else int(previous[1]) + 1
        if parent_version_id is not None:
            parent_version = int(parent_version_id)
        else:
            parent_version = None if previous is None else int(previous[0])

        self.connection.execute(
            """
            INSERT INTO analysis_versions (
                id, analysis_name, version, parent_version, branch, dataset,
                filters, order_by, selected_columns, model_type, y, x
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                int(next_id),
                analysis_name,
                next_version,
                parent_version,
                branch,
                dataset,
                json.dumps(filters),
                json.dumps(order_by) if order_by is not None else None,
                json.dumps(selected_columns) if selected_columns is not None else None,
                model_type,
                y,
                json.dumps(x),
            ],
        )
        return {
            "id": int(next_id),
            "analysis_name": analysis_name,
            "version": next_version,
            "parent_version": parent_version,
            "branch": branch,
        }

    def list_analysis_versions(self, analysis_name: str) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT id, analysis_name, version, parent_version, branch, dataset,
                   filters, order_by, selected_columns, model_type, y, x, created_at
            FROM analysis_versions
            WHERE analysis_name = ?
            ORDER BY version DESC
            """,
            [analysis_name],
        ).fetchall()
        return [
            {
                "id": row[0],
                "analysis_name": row[1],
                "version": row[2],
                "parent_version": row[3],
                "branch": row[4] or "main",
                "dataset": row[5],
                "filters": json.loads(row[6]) if row[6] else [],
                "order_by": json.loads(row[7]) if row[7] else None,
                "selected_columns": json.loads(row[8]) if row[8] else None,
                "model_type": row[9],
                "y": row[10],
                "x": json.loads(row[11]) if row[11] else [],
                "created_at": row[12],
            }
            for row in rows
        ]

    def list_all_versions(self) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT id, analysis_name, version, parent_version, branch, dataset,
                   filters, order_by, selected_columns, model_type, y, x, created_at
            FROM analysis_versions
            ORDER BY analysis_name ASC, version DESC
            """
        ).fetchall()
        return [
            {
                "id": row[0],
                "analysis_name": row[1],
                "version": row[2],
                "parent_version": row[3],
                "branch": row[4] or "main",
                "dataset": row[5],
                "filters": json.loads(row[6]) if row[6] else [],
                "order_by": json.loads(row[7]) if row[7] else None,
                "selected_columns": json.loads(row[8]) if row[8] else None,
                "model_type": row[9],
                "y": row[10],
                "x": json.loads(row[11]) if row[11] else [],
                "created_at": row[12],
            }
            for row in rows
        ]

    def get_analysis_version(self, version_id: int) -> dict | None:
        row = self.connection.execute(
            """
            SELECT id, analysis_name, version, parent_version, branch, dataset,
                   filters, order_by, selected_columns, model_type, y, x, created_at
            FROM analysis_versions
            WHERE id = ?
            """,
            [int(version_id)],
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "analysis_name": row[1],
            "version": row[2],
            "parent_version": row[3],
            "branch": row[4] or "main",
            "dataset": row[5],
            "filters": json.loads(row[6]) if row[6] else [],
            "order_by": json.loads(row[7]) if row[7] else None,
            "selected_columns": json.loads(row[8]) if row[8] else None,
            "model_type": row[9],
            "y": row[10],
            "x": json.loads(row[11]) if row[11] else [],
            "created_at": row[12],
        }

    def execute(self, query: str, parameters: list | tuple | None = None):
        return self.connection.execute(query, parameters or [])

    def fetch_df(
        self,
        query: str,
        parameters: list | tuple | None = None,
    ) -> pd.DataFrame:
        return self.connection.execute(query, parameters or []).fetchdf()

    def fetch_one(self, query: str, parameters: list | tuple | None = None):
        return self.connection.execute(query, parameters or []).fetchone()

    def close(self) -> None:
        return None
