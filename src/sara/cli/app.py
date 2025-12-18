from __future__ import annotations

from pathlib import Path
from typing import Optional, Callable, TypeVar

import typer

from sara.orchestrator import Orchestrator

T = TypeVar("T")

# ------------------------------------------------------------
# CLI principal y sub-apps
# ------------------------------------------------------------

app = typer.Typer(help="SARA CLI (skeleton). Interfaces datasets, transforms y stats.")
dataset_app = typer.Typer(help="Crear y consultar datasets.")
import_app = typer.Typer(help="Importar datos (crea versiones inmutables).")
transform_app = typer.Typer(help="Transformaciones que generan nuevas versiones.")
stats_app = typer.Typer(help="Estadística descriptiva sobre una versión.")

app.add_typer(dataset_app, name="dataset")
app.add_typer(import_app, name="import")
app.add_typer(transform_app, name="transform")
app.add_typer(stats_app, name="stats")

# ------------------------------------------------------------
# Orchestrator (Facade)
# ------------------------------------------------------------

orc = Orchestrator()


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _parse_dataset_version(raw: str) -> tuple[str, str]:
    """Parsea '<dataset_id>:<version>' (ej: hogares_2023:v1)."""
    if ":" not in raw:
        raise typer.BadParameter("Formato esperado: <dataset_id>:<version> (ej: hogares_2023:v1)")
    dataset_id, version = raw.split(":", 1)
    return dataset_id, version


def _catch_not_implemented() -> None:
    typer.secho(
        "Esta acción está en esqueleto: falta implementar engine/storage.",
        fg=typer.colors.YELLOW,
    )


def _cli_guard(fn: Callable[[], T]) -> T:
    """Wrapper estándar para errores CLI (menos repetición)."""
    try:
        return fn()
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
        raise typer.Exit(code=1)
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


def _get_version(ref: str):
    dataset_id, version = _parse_dataset_version(ref)
    return orc.get_version(dataset_id, version)


def _print_new_version(v) -> None:
    typer.echo(f"Nueva versión: {v.dataset_id}:{v.version}")


# ------------------------------------------------------------
# dataset: create/list/show
# ------------------------------------------------------------

@dataset_app.command("create")
def dataset_create(
    dataset_id: str = typer.Option(..., "--dataset-id", "-d", help="Identificador lógico (snake_case)."),
    name: str = typer.Option(..., "--name", "-n", help="Nombre legible."),
    description: Optional[str] = typer.Option(None, "--description", "-m", help="Descripción opcional."),
):
    """Registrar un nuevo dataset lógico."""

    def run():
        dataset = orc.create_dataset(dataset_id=dataset_id, name=name, description=description)
        typer.echo(f"Dataset creado: {dataset.dataset_id} ({dataset.name})")

    _cli_guard(run)


@dataset_app.command("list")
def dataset_list():
    """Listar datasets registrados."""

    def run():
        datasets = orc.list_datasets()
        if not datasets:
            typer.echo("No hay datasets registrados.")
            raise typer.Exit(code=0)
        for ds in datasets:
            typer.echo(f"- {ds.dataset_id}: {ds.name}")

    _cli_guard(run)


@dataset_app.command("show")
def dataset_show(dataset_id: str):
    """Mostrar un dataset por id."""

    def run():
        ds = orc.get_dataset(dataset_id)
        typer.echo(f"{ds.dataset_id} :: {ds.name}")
        if ds.description:
            typer.echo(ds.description)

    _cli_guard(run)


# ------------------------------------------------------------
# import: csv/xlsx
# ------------------------------------------------------------

@import_app.command("csv")
def import_csv(
    dataset_id: str,
    csv_path: Path,
    version: str = typer.Option("v1", help="Versión que se creará (inmutable)."),
):
    """Importar un CSV y crear la primera versión en Parquet."""

    def run():
        version_obj = orc.import_csv(dataset_id=dataset_id, csv_path=csv_path, version=version)
        typer.echo(f"Versión creada: {version_obj.dataset_id}:{version_obj.version} -> {version_obj.path}")

    _cli_guard(run)


@import_app.command("xlsx")
def import_xlsx(
    dataset_id: str,
    xlsx_path: Path,
    version: str = typer.Option("v1", help="Versión que se creará (inmutable)."),
    sheet: Optional[str] = typer.Option(None, "--sheet", help="Hoja a leer (por defecto la primera)."),
):
    """Importar un Excel y crear la primera versión en Parquet."""

    def run():
        version_obj = orc.import_xlsx(dataset_id=dataset_id, xlsx_path=xlsx_path, version=version, sheet=sheet)
        typer.echo(f"Versión creada: {version_obj.dataset_id}:{version_obj.version} -> {version_obj.path}")

    _cli_guard(run)


# ------------------------------------------------------------
# preview / profile (top-level)
# ------------------------------------------------------------

@app.command("preview")
def preview(
    dataset_version: str,
    limit: int = typer.Option(100, "--limit", "-l", help="Filas a mostrar (<=100)."),
):
    """Preview controlado de una versión."""
    if limit > 100:
        raise typer.BadParameter("limit máximo es 100 (ajustar CLI si querés más).")

    def run():
        dv = _get_version(dataset_version)
        rows = orc.preview(dv, limit=limit)
        typer.echo(f"Preview de {dataset_version} (primeras {limit} filas):")
        for row in rows:
            typer.echo(str(row))

    _cli_guard(run)


@app.command("profile")
def profile(dataset_version: str):
    """Perfilado básico de columnas."""

    def run():
        dv = _get_version(dataset_version)
        profile_data = orc.profile(dv)
        typer.echo(profile_data)

    _cli_guard(run)


# ------------------------------------------------------------
# transform: filter / winsorize / recode
# ------------------------------------------------------------

@transform_app.command("filter")
def transform_filter(
    dataset_version: str,
    where: str = typer.Option(..., "--where", help="Condición SQL-ish."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    """Filtrar filas y generar nueva versión."""

    def run():
        dv = _get_version(dataset_version)
        new_version = orc.filter(dataset_version=dv, where=where, out_version=out_version)
        _print_new_version(new_version)

    _cli_guard(run)


@transform_app.command("winsorize")
def transform_winsorize(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna a winsorizar."),
    p_low: float = typer.Option(0.01, "--p-low", help="Percentil inferior."),
    p_high: float = typer.Option(0.99, "--p-high", help="Percentil superior."),
    out_column: Optional[str] = typer.Option(None, "--out-col", help="Columna de salida (default: reemplaza)."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    """Winsorizar columna y generar nueva versión."""

    def run():
        dv = _get_version(dataset_version)
        new_version = orc.winsorize(
            dataset_version=dv,
            column=column,
            p_low=p_low,
            p_high=p_high,
            out_column=out_column,
            out_version=out_version,
        )
        _print_new_version(new_version)

    _cli_guard(run)


@transform_app.command("recode")
def transform_recode(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna a recodificar."),
    mapping: str = typer.Option(..., "--map", help="JSON mapping ej: '{\"M\":1,\"F\":0}'."),
    out_column: Optional[str] = typer.Option(None, "--out-col", help="Columna de salida (default: reemplaza)."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    """Recodificar columna con mapping JSON y generar nueva versión."""

    def run():
        import json

        mapping_dict = json.loads(mapping)
        dv = _get_version(dataset_version)
        new_version = orc.recode(
            dataset_version=dv,
            column=column,
            mapping=mapping_dict,
            out_column=out_column,
            out_version=out_version,
        )
        _print_new_version(new_version)

    try:
        _cli_guard(run)
    except Exception as exc:  # noqa: BLE001
        # Mantener mensaje especial para JSON inválido si aparece
        if "JSONDecodeError" in exc.__class__.__name__:
            typer.secho(f"Mapping inválido: {exc}", fg=typer.colors.RED)
            raise typer.Exit(code=1) from exc
        raise


# ------------------------------------------------------------
# stats: mean
# ------------------------------------------------------------

@stats_app.command("mean")
def stats_mean(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna objetivo."),
    where: Optional[str] = typer.Option(None, "--where", help="Filtro opcional."),
):
    """Calcular media de una columna (con filtro opcional)."""

    def run():
        dv = _get_version(dataset_version)
        result = orc.mean(dataset_version=dv, column=column, where=where)
        typer.echo(f"Mean({column}) = {result}")

    _cli_guard(run)


# ------------------------------------------------------------
# Extras: run/debug-state (skeleton)
# ------------------------------------------------------------

@app.command("run")
def run_from_spec(spec_path: Path):
    """Ejecutar una spec JSON/YAML (placeholder)."""

    def run():
        typer.echo(f"Leer spec: {spec_path} (pendiente de implementación)")
        _catch_not_implemented()

    _cli_guard(run)


@app.command("debug-state")
def debug_state():
    """Imprimir estado en memoria del repositorio (útil en skeleton)."""

    def run():
        typer.echo(orc.repository.as_debug_dict())

    _cli_guard(run)


if __name__ == "__main__":
    app()
