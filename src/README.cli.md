# CLI (borrador)

Andamiaje inicial del CLI de SARA. No implementa lógica de negocio; define la estructura de comandos, módulos y servicios para iterar luego.

## Estructura

- `sara/core`: modelos de dominio mínimos.
- `sara/engine`: punto de entrada para DuckDB u otros motores.
- `sara/storage`: capa de acceso a metadatos y datasets.
- `sara/orchestrator`: servicios de alto nivel usados por CLI/API.
- `sara/cli`: comandos Typer agrupados por dominio.

## Uso rápido

Ejecuta desde la raíz del repo (no desde `src/`), agregando `PYTHONPATH=src` para que Python encuentre el paquete:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m sara.cli.app --help
PYTHONPATH=src python -m sara.cli.app dataset create --name "Hogares 2023" --dataset-id hogares_2023
PYTHONPATH=src python -m sara.cli.app dataset list
```

Si prefieres evitar `PYTHONPATH`, puedes hacer:

```bash
cd src
python -m sara.cli.app --help
```

Los comandos actuales devuelven mensajes de "pending implementation" pero mantienen la interfaz prevista para el MVP real.
