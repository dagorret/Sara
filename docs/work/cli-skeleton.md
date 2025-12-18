# CLI Skeleton (Typer) — estado

Este borrador describe el andamiaje inicial del CLI creado en `src/sara/`. Es un esqueleto: no ejecuta lógica real, pero define estructura, comandos y puntos de extensión.

## Estructura creada

- `src/sara/core/`: modelos de dominio (`Dataset`, `DatasetVersion`, `Operation`, `Run`).
- `src/sara/engine/duck.py`: stub del motor DuckDB, con métodos declarados para import, preview, profile, filter, winsorize, recode y mean.
- `src/sara/storage/repository.py`: repositorio en memoria para datasets, versiones y operaciones (para probar el CLI sin Postgres).
- `src/sara/orchestrator/service.py`: orquestador que coordina repositorio + engine y expone operaciones de alto nivel.
- `src/sara/cli/app.py`: CLI con Typer; comandos agrupados por dominio (`dataset`, `import`, `transform`, `stats`, `run`, `debug-state`).
- `src/README.cli.md`: notas rápidas de uso y objetivo del skeleton.
- `requirements.txt`: se añadió `typer>=0.9.0` para habilitar el CLI.

## Comandos disponibles (stubs)

- `dataset create/list/show`
- `import csv|xlsx` (implementado con DuckDB → Parquet; requiere deps instaladas)
- `preview`, `profile`
- `transform filter|winsorize|recode`
- `stats mean`
- `run` (desde spec)
- `debug-state` (imprime el repositorio en memoria)

Los comandos validan parámetros y reportan “pending implementation” en los puntos aún no cubiertos por el engine.

Para ejecutarlos desde la raíz del repo:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m sara.cli.app --help
```

## Qué falta implementar

- Lógica real en `DuckDBEngine` (lectura CSV/XLSX → Parquet, preview, perfilado, transformaciones, stats).
- Persistencia en Postgres reemplazando el repositorio en memoria.
- Definir layout definitivo de paths de datasets/versions y manejo de artifacts.
- Tests automáticos para comandos y servicios.
