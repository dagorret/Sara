from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import duckdb


class DuckDBEngine:
    """
    Engine basado en DuckDB.

    Cambios importantes vs tu versión actual:
      1) NO construye rutas "out_dir" por su cuenta.
         El path destino lo resuelve StorageLayout (o quien lo llame).
      2) SIEMPRE cierra conexiones (with duckdb.connect()).
      3) Evita f-strings con paths en SQL (mejor robustez).
      4) Implementa preview / filter / mean para que el CLI funcione.
    """

    def __init__(self, database: str = ":memory:") -> None:
        # database puede ser ":memory:" o una ruta a un archivo .duckdb
        self.database = database

    # ---------------------------
    # Importación
    # ---------------------------

    def import_csv(self, csv_path: Path, out_path: Path) -> Path:
        """
        Importa CSV a Parquet.

        NOTA (seguridad/robustez):
          - no usamos f-string con paths para evitar problemas con comillas.
          - validamos existencia del CSV.
          - creamos directorio del out_path.

        Contrato:
          - devuelve out_path (parquet generado)
        """
        csv_path = Path(csv_path)
        out_path = Path(out_path)

        if not csv_path.is_file():
            raise FileNotFoundError(f"CSV no encontrado: {csv_path}")

        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Usamos una conexión efímera. Para alto rendimiento podrías mantener
        # una conexión viva, pero para CLI simple es mejor evitar estado oculto.
        with duckdb.connect(self.database) as con:
            # DuckDB permite bind de parámetros para valores.
            # read_csv_auto(?) acepta el path como parámetro.
            con.execute(
                """
                COPY (
                    SELECT *
                    FROM read_csv_auto(?)
                )
                TO ?
                (FORMAT PARQUET);
                """,
                [str(csv_path), str(out_path)],
            )

        return out_path

    def import_xlsx(self, xlsx_path: Path, out_path: Path, sheet: str | None = None) -> Path:
        """
        Importa Excel a Parquet usando read_excel.

        Nota:
          - read_excel puede requerir extensión/soporte según versión/config.
          - `sheet` es opcional: si es None, se lee la primera hoja.

        Importante:
          - el parámetro "sheet" no se puede bindear tan fácil dentro de la función
            read_excel; por eso armamos el SQL con cuidado.
          - En este punto, sheet viene del usuario. En CLI real podrías validarlo
            (por ejemplo permitir solo nombres alfanuméricos/espacios).
        """
        xlsx_path = Path(xlsx_path)
        out_path = Path(out_path)

        if not xlsx_path.is_file():
            raise FileNotFoundError(f"XLSX no encontrado: {xlsx_path}")

        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Armamos la cláusula de sheet de forma controlada.
        # Si querés ultra-robustez, escapá comillas simples en sheet.
        if sheet is not None:
            safe_sheet = sheet.replace("'", "''")
            sheet_clause = f", sheet='{safe_sheet}'"
        else:
            sheet_clause = ""

        with duckdb.connect(self.database) as con:
            con.execute(
                f"""
                COPY (
                    SELECT *
                    FROM read_excel(?{sheet_clause})
                )
                TO ?
                (FORMAT PARQUET);
                """,
                [str(xlsx_path), str(out_path)],
            )

        return out_path

    # ---------------------------
    # Consultas básicas
    # ---------------------------

    def preview(self, dataset_version_path: Path, limit: int = 100) -> Iterable[dict[str, Any]]:
        """
        Preview simple: devuelve filas como dict (col -> valor).

        Comentario:
          - Para CLI, dict es más cómodo.
          - Limitamos en SQL con LIMIT ? (bind param).
        """
        dataset_version_path = Path(dataset_version_path)
        if not dataset_version_path.is_file():
            raise FileNotFoundError(f"Parquet no encontrado: {dataset_version_path}")

        if limit <= 0:
            return []

        with duckdb.connect(self.database) as con:
            cur = con.execute(
                "SELECT * FROM read_parquet(?) LIMIT ?;",
                [str(dataset_version_path), int(limit)],
            )
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]  # nombres columnas

        return [dict(zip(cols, row)) for row in rows]

    def filter(self, dataset_version_path: Path, where: str, out_version_path: Path) -> Path:
        """
        Filtra filas con una condición SQL-ish (where) y escribe un nuevo parquet.

        Importante:
          - `where` se inserta como texto SQL, NO puede bindearse como parámetro.
            Esto significa que es responsabilidad del caller (CLI) y del diseño
            aceptar que `where` es "código" SQL.
          - Para un producto final, podrías:
              (a) validar/parsear un subset del lenguaje
              (b) o construir expresiones seguras
            Pero para un CLI tipo data-tool, suele aceptarse SQL.

        También:
          - Aseguramos directorio del out_version_path.
        """
        dataset_version_path = Path(dataset_version_path)
        out_version_path = Path(out_version_path)

        if not dataset_version_path.is_file():
            raise FileNotFoundError(f"Parquet no encontrado: {dataset_version_path}")

        out_version_path.parent.mkdir(parents=True, exist_ok=True)

        # Escapamos comillas simples en where? NO sirve: where es expresión SQL.
        # Lo correcto es tratarlo como "SQL user input" y documentarlo.
        with duckdb.connect(self.database) as con:
            # read_parquet(path) sí lo pasamos como parámetro
            # pero el WHERE se interpolará.
            con.execute(
                f"""
                COPY (
                    SELECT *
                    FROM read_parquet(?)
                    WHERE {where}
                )
                TO ?
                (FORMAT PARQUET);
                """,
                [str(dataset_version_path), str(out_version_path)],
            )

        return out_version_path

    def mean(self, dataset_version_path: Path, column: str, where: str | None = None) -> float:
        """
        Calcula promedio (AVG) de una columna.

        Detalles:
          - El nombre de columna NO se puede bindear como parámetro en SQL estándar.
            Por eso interpolamos `column` como identificador.
          - Esto requiere validación mínima para evitar SQL injection accidental.

        En un CLI interno, con columnas reales, alcanza validar:
          - column debe ser alfanumérico + underscore (snake_case) o similar.
        """
        dataset_version_path = Path(dataset_version_path)
        if not dataset_version_path.is_file():
            raise FileNotFoundError(f"Parquet no encontrado: {dataset_version_path}")

        # Validación mínima de identificador.
        # Si querés permitir columnas con espacios, habría que quotearlas con "..."
        if not column.replace("_", "").isalnum():
            raise ValueError(f"Nombre de columna inválido: {column!r}")

        where_clause = f"WHERE {where}" if where else ""

        with duckdb.connect(self.database) as con:
            cur = con.execute(
                f"""
                SELECT AVG({column}) AS mean_value
                FROM read_parquet(?)
                {where_clause};
                """,
                [str(dataset_version_path)],
            )
            (value,) = cur.fetchone()

        # DuckDB puede devolver None si no hay filas o todo es NULL.
        if value is None:
            raise ValueError("Mean es NULL (sin filas o todos los valores son NULL).")

        return float(value)

    # ---------------------------
    # Stubs pendientes (tu roadmap)
    # ---------------------------

    def profile(self, dataset_version_path: Path) -> dict[str, Any]:
        raise NotImplementedError("Profile not implemented yet.")

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