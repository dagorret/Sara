from __future__ import annotations

from dataclasses import dataclass, field, replace
import logging
import re

import duckdb
import pandas as pd

from .config import DEFAULT_PAGE_SIZE
from .database import quote_identifier
from .exceptions import QueryError, ValidationError


log = logging.getLogger(__name__)

_NUMERIC_TYPES = {
    "bigint",
    "double",
    "decimal",
    "float",
    "hugeint",
    "integer",
    "int",
    "numeric",
    "real",
    "smallint",
    "tinyint",
    "ubigint",
    "uinteger",
    "usmallint",
    "utinyint",
}
_DANGEROUS_SQL_TOKENS = (";", "--", "/*", "*/")


@dataclass(frozen=True, slots=True)
class Dataset:
    connection: duckdb.DuckDBPyConnection
    base_table: str
    path: str = ""
    filters: tuple[str, ...] = ()
    ordering: tuple[str, bool] | None = None
    selected_columns: tuple[str, ...] | None = None
    column_aliases: tuple[tuple[str, str], ...] = ()
    _last_query: str | None = field(default=None, compare=False, repr=False)
    _last_result: pd.DataFrame | None = field(default=None, compare=False, repr=False)

    @property
    def table_name(self) -> str:
        return self.base_table

    def filter(self, condition: str) -> Dataset:
        normalized = self._normalize_filter_condition(condition)
        if not normalized:
            return self
        log.info("Applying dataset filter on '%s': %s", self.base_table, normalized)
        return replace(self, filters=(*self.filters, normalized), _last_query=None, _last_result=None)

    def order_by(self, column: str, ascending: bool = True) -> Dataset:
        resolved = self.resolve_column(column)
        log.info("Ordering dataset '%s' by %s %s", self.base_table, resolved, "ASC" if ascending else "DESC")
        return replace(
            self,
            ordering=(resolved, bool(ascending)),
            _last_query=None,
            _last_result=None,
        )

    def select(self, columns: list[str] | tuple[str, ...] | None) -> Dataset:
        if not columns:
            return replace(self, selected_columns=None, _last_query=None, _last_result=None)
        normalized = tuple(self.resolve_column(column) for column in columns)
        log.info("Selecting columns on '%s': %s", self.base_table, list(normalized))
        return replace(
            self,
            selected_columns=normalized,
            _last_query=None,
            _last_result=None,
        )

    def with_aliases(self, aliases: dict[str, str] | None) -> Dataset:
        if not aliases:
            return self
        normalized = tuple((str(key), self.resolve_column(value)) for key, value in aliases.items())
        return replace(self, column_aliases=normalized)

    def clear_filters(self) -> Dataset:
        return replace(self, filters=(), _last_query=None, _last_result=None)

    def clear_ordering(self) -> Dataset:
        return replace(self, ordering=None, _last_query=None, _last_result=None)

    def reset_query(self) -> Dataset:
        return replace(
            self,
            filters=(),
            ordering=None,
            selected_columns=None,
            _last_query=None,
            _last_result=None,
        )

    def get_shape(self) -> tuple[int, int]:
        sql = f"SELECT COUNT(*) FROM {quote_identifier(self.base_table)}"
        where_clause = self._build_where_clause()
        if where_clause:
            sql += f" WHERE {where_clause}"
        row_count = self.scalar(sql)
        return int(row_count or 0), len(self.get_columns())

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

    def get_metadata(self) -> dict[str, object]:
        log.info("Collecting metadata for dataset '%s'", self.base_table)
        columns = self.get_base_columns()
        rows = self.connection.execute(
            f"PRAGMA table_info({quote_identifier(self.base_table)})"
        ).fetchall()
        types = {row[1]: str(row[2]).lower() for row in rows}
        row_count = self.scalar(
            f"SELECT COUNT(*) FROM {quote_identifier(self.base_table)}"
        ) or 0

        null_counts: dict[str, int] = {}
        cardinality: dict[str, int] = {}
        stats: dict[str, dict[str, float | None]] = {}

        for column in columns:
            column_ref = quote_identifier(column)
            null_counts[column] = int(
                self.scalar(
                    f"SELECT COUNT(*) FROM {quote_identifier(self.base_table)} WHERE {column_ref} IS NULL"
                )
                or 0
            )
            cardinality[column] = int(
                self.scalar(
                    f"SELECT COUNT(DISTINCT {column_ref}) FROM {quote_identifier(self.base_table)}"
                )
                or 0
            )
            if self._is_numeric_type(types[column]):
                row = self.connection.execute(
                    f"""
                    SELECT AVG({column_ref}) AS mean_value, STDDEV_SAMP({column_ref}) AS std_value
                    FROM {quote_identifier(self.base_table)}
                    """
                ).fetchone()
                stats[column] = {
                    "mean": None if row is None or row[0] is None else float(row[0]),
                    "std": None if row is None or row[1] is None else float(row[1]),
                }
            else:
                stats[column] = {"mean": None, "std": None}

        return {
            "table": self.base_table,
            "path": self.path,
            "rows": int(row_count),
            "columns": columns,
            "types": types,
            "null_counts": null_counts,
            "cardinality": cardinality,
            "stats": stats,
        }

    def get_preview(self, limit: int = DEFAULT_PAGE_SIZE) -> pd.DataFrame:
        return self.query(limit=limit, offset=0)

    def get_page(self, limit: int, offset: int) -> pd.DataFrame:
        return self.query(limit=limit, offset=offset)

    def build_query(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> str:
        select_clause = self._build_select_clause()
        query = f"SELECT {select_clause} FROM {quote_identifier(self.base_table)}"

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
        sql = self.build_query(limit=limit, offset=offset)
        if sql == self._last_query and self._last_result is not None:
            log.info("Returning cached query result for dataset '%s'", self.base_table)
            return self._last_result.copy()

        try:
            log.info("Executing query on dataset '%s': %s", self.base_table, sql)
            result = self.connection.execute(sql).fetchdf()
        except Exception as exc:
            log.error("Query execution failed on dataset '%s': %s", self.base_table, exc)
            raise QueryError(f"No se pudo ejecutar la consulta del dataset '{self.base_table}'.") from exc

        object.__setattr__(self, "_last_query", sql)
        object.__setattr__(self, "_last_result", result.copy())
        return result

    def scalar(self, sql: str, parameters: list | tuple | None = None):
        try:
            row = self.connection.execute(sql, parameters or []).fetchone()
        except Exception as exc:
            log.error("Scalar query failed on dataset '%s': %s", self.base_table, exc)
            raise QueryError("No se pudo ejecutar la consulta escalar solicitada.") from exc
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
            "column_aliases": dict(self.column_aliases),
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
        aliases = state.get("column_aliases") or {}
        return cls(
            connection=connection,
            base_table=state["base_table"],
            path=state.get("path", ""),
            filters=tuple(state.get("filters", [])),
            ordering=ordering,
            selected_columns=None if selected_columns is None else tuple(selected_columns),
            column_aliases=tuple((str(key), str(value)) for key, value in aliases.items()),
        )

    def resolve_column(self, column: str) -> str:
        normalized = str(column).strip()
        aliases = dict(self.column_aliases)
        candidate = aliases.get(normalized, normalized)
        available = set(self.get_base_columns())
        if candidate not in available:
            raise ValidationError(
                f"Columna no encontrada en '{self.base_table}': '{column}'."
            )
        return candidate

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

    def _normalize_filter_condition(self, condition: str) -> str:
        raw_condition = str(condition).strip()
        if not raw_condition:
            return ""

        for token in _DANGEROUS_SQL_TOKENS:
            if token in raw_condition:
                raise ValidationError("El filtro contiene tokens SQL no permitidos.")

        null_match = re.match(
            r"^(?P<column>[A-Za-z_][A-Za-z0-9_]*)\s+IS\s+(?P<negation>NOT\s+)?NULL$",
            raw_condition,
            flags=re.IGNORECASE,
        )
        if null_match:
            column = self.resolve_column(null_match.group("column"))
            negation = "NOT " if null_match.group("negation") else ""
            return f"{quote_identifier(column)} IS {negation}NULL"

        like_match = re.match(
            r"^(?P<column>[A-Za-z_][A-Za-z0-9_]*)\s+LIKE\s+(?P<value>.+)$",
            raw_condition,
            flags=re.IGNORECASE,
        )
        if like_match:
            column = self.resolve_column(like_match.group("column"))
            value = self._sanitize_literal(like_match.group("value"))
            return f"{quote_identifier(column)} LIKE {value}"

        in_match = re.match(
            r"^(?P<column>[A-Za-z_][A-Za-z0-9_]*)\s+IN\s*\((?P<values>.+)\)$",
            raw_condition,
            flags=re.IGNORECASE,
        )
        if in_match:
            column = self.resolve_column(in_match.group("column"))
            values = [self._sanitize_literal(value.strip()) for value in in_match.group("values").split(",")]
            if not values:
                raise ValidationError("El filtro IN debe contener al menos un valor.")
            return f"{quote_identifier(column)} IN ({', '.join(values)})"

        comparison_match = re.match(
            r"^(?P<column>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<operator>=|!=|<>|>=|<=|>|<)\s*(?P<value>.+)$",
            raw_condition,
        )
        if comparison_match:
            column = self.resolve_column(comparison_match.group("column"))
            operator = comparison_match.group("operator")
            value = self._sanitize_literal(comparison_match.group("value"))
            return f"{quote_identifier(column)} {operator} {value}"

        raise ValidationError(
            "Filtro no soportado. Use expresiones simples como 'columna >= 10', "
            "'columna = valor', 'columna IN (...)', 'columna LIKE ...' o 'columna IS NULL'."
        )

    def _sanitize_literal(self, raw_value: str) -> str:
        value = raw_value.strip()
        if not value:
            raise ValidationError("El filtro contiene un valor vacío.")

        if any(token in value for token in _DANGEROUS_SQL_TOKENS):
            raise ValidationError("El valor del filtro contiene tokens SQL no permitidos.")

        upper_value = value.upper()
        if upper_value == "NULL":
            return "NULL"
        if upper_value in {"TRUE", "FALSE"}:
            return upper_value

        if re.fullmatch(r"[-+]?\d+(\.\d+)?", value):
            return value

        if value.startswith("'") and value.endswith("'") and len(value) >= 2:
            inner = value[1:-1]
        elif value.startswith('"') and value.endswith('"') and len(value) >= 2:
            inner = value[1:-1]
        else:
            inner = value

        return "'" + inner.replace("'", "''") + "'"

    @staticmethod
    def _is_numeric_type(dtype: str) -> bool:
        normalized = str(dtype).lower()
        return any(token in normalized for token in _NUMERIC_TYPES)
