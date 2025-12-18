from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from sara.orchestrator import Orchestrator

app = typer.Typer(help="SARA CLI (skeleton). Interfaces datasets, transforms y stats.")
dataset_app = typer.Typer(help="Crear y consultar datasets.")
import_app = typer.Typer(help="Importar datos (crea versiones inmutables).")
transform_app = typer.Typer(help="Transformaciones que generan nuevas versiones.")
stats_app = typer.Typer(help="Estadística descriptiva sobre una versión.")

app.add_typer(dataset_app, name="dataset")
app.add_typer(import_app, name="import")
app.add_typer(transform_app, name="transform")
app.add_typer(stats_app, name="stats")

orc = Orchestrator()


def _parse_dataset_version(raw: str):
    if ":" not in raw:
        raise typer.BadParameter("Formato esperado: <dataset_id>:<version> (ej: hogares_2023:v1)")
    dataset_id, version = raw.split(":", 1)
    return dataset_id, version


def _catch_not_implemented():
    typer.secho("Esta acción está en esqueleto: falta implementar engine/storage.", fg=typer.colors.YELLOW)


@dataset_app.command("create")
def dataset_create(
    dataset_id: str = typer.Option(..., "--dataset-id", "-d", help="Identificador lógico (snake_case)."),
    name: str = typer.Option(..., "--name", "-n", help="Nombre legible."),
    description: Optional[str] = typer.Option(None, "--description", "-m", help="Descripción opcional."),
):
    """Registrar un nuevo dataset lógico."""
    try:
        dataset = orc.create_dataset(dataset_id=dataset_id, name=name, description=description)
        typer.echo(f"Dataset creado: {dataset.dataset_id} ({dataset.name})")
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@dataset_app.command("list")
def dataset_list():
    """Listar datasets registrados."""
    datasets = orc.list_datasets()
    if not datasets:
        typer.echo("No hay datasets registrados.")
        raise typer.Exit(code=0)
    for ds in datasets:
        typer.echo(f"- {ds.dataset_id}: {ds.name}")


@dataset_app.command("show")
def dataset_show(dataset_id: str):
    """Mostrar un dataset por id."""
    try:
        ds = orc.get_dataset(dataset_id)
        typer.echo(f"{ds.dataset_id} :: {ds.name}")
        if ds.description:
            typer.echo(ds.description)
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@import_app.command("csv")
def import_csv(
    dataset_id: str,
    csv_path: Path,
    version: str = typer.Option("v1", help="Versión que se creará (inmutable)."),
):
    """Importar un CSV y crear la primera versión en Parquet."""
    try:
        version_obj = orc.import_csv(dataset_id=dataset_id, csv_path=csv_path, version=version)
        typer.echo(f"Versión creada: {version_obj.dataset_id}:{version_obj.version} -> {version_obj.path}")
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@import_app.command("xlsx")
def import_xlsx(
    dataset_id: str,
    xlsx_path: Path,
    version: str = typer.Option("v1", help="Versión que se creará (inmutable)."),
    sheet: Optional[str] = typer.Option(None, "--sheet", help="Hoja a leer (por defecto la primera)."),
):
    """Importar un Excel y crear la primera versión en Parquet."""
    try:
        version_obj = orc.import_xlsx(dataset_id=dataset_id, xlsx_path=xlsx_path, version=version, sheet=sheet)
        typer.echo(f"Versión creada: {version_obj.dataset_id}:{version_obj.version} -> {version_obj.path}")
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("preview")
def preview(dataset_version: str, limit: int = typer.Option(100, "--limit", "-l", help="Filas a mostrar (<=100).")):
    """Preview controlado de una versión."""
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        dv = orc.repository.get_version(dataset_id, version)
        rows = orc.preview(dv, limit=limit)
        typer.echo(f"Preview de {dataset_id}:{version} (primeras {limit} filas):")
        for row in rows:
            typer.echo(str(row))
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("profile")
def profile(dataset_version: str):
    """Perfilado básico de columnas."""
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        dv = orc.repository.get_version(dataset_id, version)
        profile_data = orc.profile(dv)
        typer.echo(profile_data)
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@transform_app.command("filter")
def transform_filter(
    dataset_version: str,
    where: str = typer.Option(..., "--where", help="Condición SQL-ish."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    """Filtrar filas y generar nueva versión."""
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        dv = orc.repository.get_version(dataset_id, version)
        new_version = orc.filter(dataset_version=dv, where=where, out_version=out_version)
        typer.echo(f"Nueva versión: {new_version.dataset_id}:{new_version.version}")
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@transform_app.command("winsorize")
def transform_winsorize(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna a winsorizar."),
    p_low: float = typer.Option(0.01, "--p-low", help="Percentil inferior."),
    p_high: float = typer.Option(0.99, "--p-high", help="Percentil superior."),
    out_column: Optional[str] = typer.Option(None, "--out-col", help="Columna de salida (default: reemplaza)."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        dv = orc.repository.get_version(dataset_id, version)
        new_version = orc.winsorize(
            dataset_version=dv,
            column=column,
            p_low=p_low,
            p_high=p_high,
            out_column=out_column,
            out_version=out_version,
        )
        typer.echo(f"Nueva versión: {new_version.dataset_id}:{new_version.version}")
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@transform_app.command("recode")
def transform_recode(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna a recodificar."),
    mapping: str = typer.Option(..., "--map", help="JSON mapping ej: '{\"M\":1,\"F\":0}'."),
    out_column: Optional[str] = typer.Option(None, "--out-col", help="Columna de salida (default: reemplaza)."),
    out_version: str = typer.Option(..., "--out-version", help="Nueva versión (ej: v2)."),
):
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        import json

        mapping_dict = json.loads(mapping)
        dv = orc.repository.get_version(dataset_id, version)
        new_version = orc.recode(
            dataset_version=dv,
            column=column,
            mapping=mapping_dict,
            out_column=out_column,
            out_version=out_version,
        )
        typer.echo(f"Nueva versión: {new_version.dataset_id}:{new_version.version}")
    except json.JSONDecodeError as exc:
        typer.secho(f"Mapping inválido: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@stats_app.command("mean")
def stats_mean(
    dataset_version: str,
    column: str = typer.Option(..., "--col", help="Columna objetivo."),
    where: Optional[str] = typer.Option(None, "--where", help="Filtro opcional."),
):
    dataset_id, version = _parse_dataset_version(dataset_version)
    try:
        dv = orc.repository.get_version(dataset_id, version)
        result = orc.mean(dataset_version=dv, column=column, where=where)
        typer.echo(f"Mean({column}) = {result}")
    except KeyError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc
    except NotImplementedError:
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("run")
def run_from_spec(spec_path: Path):
    """Ejecutar una spec JSON/YAML (placeholder)."""
    try:
        typer.echo(f"Leer spec: {spec_path} (pendiente de implementación)")
        _catch_not_implemented()
    except Exception as exc:  # noqa: BLE001
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=1) from exc


@app.command("debug-state")
def debug_state():
    """Imprimir estado en memoria del repositorio (útil en skeleton)."""
    typer.echo(orc.repository.as_debug_dict())


if __name__ == "__main__":
    app()
