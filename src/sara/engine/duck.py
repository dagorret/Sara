from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import duckdb


class DuckDBEngine:
    """DuckDB-backed engine for imports and transformations."""

    def __init__(self, base_dir: Path | str = "data") -> None:
        self.base_dir = Path(base_dir)

    def import_csv(self, dataset_id: str, csv_path: Path, version: str = "v1") -> Path:
        csv_path = Path(csv_path)
        if not csv_path.is_file():
            raise FileNotFoundError(f"CSV no encontrado: {csv_path}")
        out_dir = self.base_dir / "datasets" / dataset_id / version
        out_dir.mkdir(parents=True, exist_ok=True)
        out_parquet = out_dir / "data.parquet"

        con = duckdb.connect()
        # DuckDB lee el CSV y escribe Parquet directamente
        con.execute(
            f"""
            COPY (
                SELECT *
                FROM read_csv_auto('{csv_path}')
            )
            TO '{out_parquet}'
            (FORMAT PARQUET);
            """
        )
        return out_parquet

    def import_xlsx(
        self,
        dataset_id: str,
        xlsx_path: Path,
        sheet: str | None,
        version: str = "v1",
    ) -> Path:
        xlsx_path = Path(xlsx_path)
        if not xlsx_path.is_file():
            raise FileNotFoundError(f"XLSX no encontrado: {xlsx_path}")
        out_dir = self.base_dir / "datasets" / dataset_id / version
        out_dir.mkdir(parents=True, exist_ok=True)
        out_parquet = out_dir / "data.parquet"

        sheet_clause = f", sheet='{sheet}'" if sheet else ""
        con = duckdb.connect()
        con.execute(
            f"""
            COPY (
                SELECT *
                FROM read_excel('{xlsx_path}'{sheet_clause})
            )
            TO '{out_parquet}'
            (FORMAT PARQUET);
            """
        )
        return out_parquet

    def preview(self, dataset_version_path: Path, limit: int = 100) -> Iterable[dict[str, Any]]:
        raise NotImplementedError("Preview not implemented yet.")

    def profile(self, dataset_version_path: Path) -> dict[str, Any]:
        raise NotImplementedError("Profile not implemented yet.")

    def filter(self, dataset_version_path: Path, where: str, out_version_path: Path) -> Path:
        raise NotImplementedError("Filter not implemented yet.")

    def winsorize(
        self,
        dataset_version_path: Path,
        column: str,
        p_low: float,
        p_high: float,
        out_column: str | None,
        out_version_path: Path,
    ) -> Path:
        raise NotImplementedError("Winsorize not implemented yet.")

    def recode(
        self,
        dataset_version_path: Path,
        column: str,
        mapping: dict[str, Any],
        out_column: str | None,
        out_version_path: Path,
    ) -> Path:
        raise NotImplementedError("Recode not implemented yet.")

    def mean(self, dataset_version_path: Path, column: str, where: str | None) -> float:
        raise NotImplementedError("Mean calculation not implemented yet.")
