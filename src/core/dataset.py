from __future__ import annotations

from dataclasses import dataclass, replace

import duckdb
import pandas as pd

from .database import quote_identifier


@dataclass(frozen=True, slots=True)
class Dataset:
    connection: duckdb.DuckDBPyConnection
    base_table: str
    path: str = ""
    filters: tuple[str, ...] = ()
    ordering: tuple[str, bool] | None = None
    selected_columns: tuple[str, ...] | None = None

    @property
    def table_name(self) -> str:
        return self.base_table

    def filter(self, condition: str) -> Dataset:
        normalized = condition.strip()
        if not normalized:
            return self
        return replace(self, filters=(*self.filters, normalized))

    def order_by(self, column: str, ascending: bool = True) -> Dataset:
        self._ensure_columns_exist([column])
        return replace(self, ordering=(column, bool(ascending)))

    def select(self, columns: list[str] | tuple[str, ...] | None) -> Dataset:
        if not columns:
            return replace(self, selected_columns=None)
        normalized = tuple(columns)
        self._ensure_columns_exist(normalized)
        return replace(self, selected_columns=normalized)

    def clear_filters(self) -> Dataset:
        return replace(self, filters=())

    def clear_ordering(self) -> Dataset:
        return replace(self, ordering=None)

    def reset_query(self) -> Dataset:
        return replace(self, filters=(), ordering=None, selected_columns=None)

    def get_shape(self) -> tuple[int, int]:
        sql = f"SELECT COUNT(*) FROM {quote_identifier(self.base_table)}"
        where_clause = self._build_where_clause()
        if where_clause:
            sql += f" WHERE {where_clause}"
        row_count = self.connection.execute(sql).fetchone()[0]
        return int(row_count), len(self.get_columns())

    def get_columns(self) -> list[str]:
        if self.selected_columns is not None:
            return list(self.selected_columns)
        return self.get_base_columns()

    def get_base_columns(self) -> list[str]:
        rows = self.connection.execute(
            f"PRAGMA table_info({quote_identifier(self.base_table)})"
        ).fetchall()
        return [row[1] for row in rows]

    def get_dtypes(self) -> dict[str, str]:
        rows = self.connection.execute(
            f"PRAGMA table_info({quote_identifier(self.base_table)})"
        ).fetchall()
        dtype_map = {row[1]: str(row[2]).lower() for row in rows}
        return {column: dtype_map[column] for column in self.get_columns()}

    def get_preview(self, limit: int = 10) -> pd.DataFrame:
        return self.query(limit=limit, offset=0)

    def get_page(self, limit: int, offset: int) -> pd.DataFrame:
        return self.query(limit=limit, offset=offset)

    def build_query(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> str:
        select_clause = self._build_select_clause()
        query = (
            f"SELECT {select_clause} FROM {quote_identifier(self.base_table)}"
        )

        where_clause = self._build_where_clause()
        if where_clause:
            query += f" WHERE {where_clause}"

        order_clause = self._build_order_clause()
        if order_clause:
            query += f" {order_clause}"

        if limit is not None:
            query += f" LIMIT {max(int(limit), 0)}"

        if offset is not None:
            query += f" OFFSET {max(int(offset), 0)}"

        return query

    def query(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> pd.DataFrame:
        return self.connection.execute(self.build_query(limit=limit, offset=offset)).fetchdf()

    def scalar(self, sql: str, parameters: list | tuple | None = None):
        row = self.connection.execute(sql, parameters or []).fetchone()
        return None if row is None else row[0]

    def get_state(self) -> dict:
        return {
            "base_table": self.base_table,
            "path": self.path,
            "filters": list(self.filters),
            "ordering": None
            if self.ordering is None
            else {"column": self.ordering[0], "ascending": self.ordering[1]},
            "selected_columns": None
            if self.selected_columns is None
            else list(self.selected_columns),
        }

    @classmethod
    def from_state(
        cls,
        connection: duckdb.DuckDBPyConnection,
        state: dict,
    ) -> Dataset:
        ordering_state = state.get("ordering")
        ordering = None
        if ordering_state:
            ordering = (
                ordering_state["column"],
                bool(ordering_state.get("ascending", True)),
            )

        selected_columns = state.get("selected_columns")
        return cls(
            connection=connection,
            base_table=state["base_table"],
            path=state.get("path", ""),
            filters=tuple(state.get("filters", [])),
            ordering=ordering,
            selected_columns=None if selected_columns is None else tuple(selected_columns),
        )

    def _build_select_clause(self) -> str:
        columns = self.selected_columns
        if not columns:
            return "*"
        return ", ".join(quote_identifier(column) for column in columns)

    def _build_where_clause(self) -> str:
        if not self.filters:
            return ""
        return " AND ".join(f"({condition})" for condition in self.filters)

    def _build_order_clause(self) -> str:
        if not self.ordering:
            return ""
        column, ascending = self.ordering
        direction = "ASC" if ascending else "DESC"
        return f"ORDER BY {quote_identifier(column)} {direction}"

    def _ensure_columns_exist(self, columns: list[str] | tuple[str, ...]) -> None:
        available = set(
            row[1]
            for row in self.connection.execute(
                f"PRAGMA table_info({quote_identifier(self.base_table)})"
            ).fetchall()
        )
        missing = [column for column in columns if column not in available]
        if missing:
            raise ValueError(f"Columnas no encontradas en '{self.base_table}': {missing}")
