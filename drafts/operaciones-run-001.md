# Separación entre Operation y Run en SARA (con entidades y meta-Python)

## 1) Distinción fundamental

**Idea**

- **Operation**: cambia/transforma datos → crea **otra DatasetVersion**
- **Run**: analiza datos (sin cambiarlos) → crea **Artifacts**

**Entidades involucradas (meta-Python)**

```python
class Dataset:
    id: "DatasetID"
    nombre: str
    descripcion: str | None
    creado_en: "Timestamp"

class DatasetVersion:
    id: "DatasetVersionID"
    dataset_id: "DatasetID"
    numero_version: int
    version_padre_id: "DatasetVersionID" | None
    ruta_parquet: "Path"
    cantidad_filas: int
    cantidad_columnas: int
    creado_en: "Timestamp"
    creado_por: str | None

class Operation:
    id: "OperationID"
    tipo: "OperationTipo"              # importar, filtrar, recodificar, derivar, winsorizar, discretizar...
    parametros: dict
    version_entrada_id: "DatasetVersionID" | None
    version_salida_id: "DatasetVersionID"
    ejecutado_en: "Timestamp"
    ejecutado_por: str | None
    sql: str | None                    # SQL usado para materializar la nueva versión (opcional pero recomendado)

class Run:
    id: "RunID"
    dataset_version_id: "DatasetVersionID"
    tipo: "RunTipo"                    # descriptivo, inferencial, econometrico
    metodo: str                        # "media", "ols", "logit", "t_test"...
    parametros: dict
    motor: str                         # "duckdb"
    sql: str                           # SQL ejecutado (auditable)
    ejecutado_en: "Timestamp"
    ejecutado_por: str | None

class Artifact:
    id: "ArtifactID"
    run_id: "RunID"
    tipo: "ArtifactTipo"               # tabla, grafico, reporte
    formato: "ArtifactFormato"         # png, pdf, xlsx, csv, latex, html
    ruta_archivo: "Path"
    creado_en: "Timestamp"
```

## 2) Qué hace Operation (transformación de datos)

**Qué representa**  
Una **transformación declarativa y determinística** que toma una `DatasetVersion` de entrada y produce una `DatasetVersion` de salida.

**Ejemplos típicos**

- `filtrar`: edad >= 18

- `recodificar`: sexo {"M":1, "F":0}

- `winsorizar`: ingreso (p1–p99)

- `discretizar`: edad en bins

- `derivar`: log_ingreso = log(ingreso)

**Entidades y contrato (meta-Python)**

`class OperationTipo: # Enum conceptual # importar | filtrar | seleccionar | recodificar | derivar | winsorizar | discretizar ... class Operation: id: "OperationID" tipo: OperationTipo # Declaración del "qué" (no del "cómo" imperativo) parametros: dict # Ejemplos: # {"where": "edad >= 18"} # {"col": "sexo", "map": {"M": 1, "F": 0}, "default": None} # {"col": "ingreso", "p_low": 0.01, "p_high": 0.99, "out_col": "ingreso_wins"} version_entrada_id: "DatasetVersionID" | None # None solo si tipo == importar version_salida_id: "DatasetVersionID" # siempre existe # Auditoría ejecutado_en: "Timestamp" ejecutado_por: str | None # Reproducibilidad técnica (recomendado) sql: str | None`

**Detalle importante**

- La salida de una Operation **es siempre una nueva versión** (nuevo Parquet).

- Operaciones **no generan artifacts** (eso es Run).

---

## 3) Qué hace Run (ejecución analítica)

**Qué representa**  
Una ejecución de análisis sobre una versión **sin modificar los datos**.

**Ejemplos típicos**

- media, mediana, varianza

- test t, chi², ANOVA

- OLS, logit, probit, panel FE, IV, DID

- generación de tablas estilo Stata

- generación de gráficos (histogramas, event study plot, RD plot)

**Entidades y contrato (meta-Python)**

`class RunTipo: # Enum conceptual # descriptivo | inferencial | econometrico ... class Run: id: "RunID" # Datos analizados (inmutables) dataset_version_id: "DatasetVersionID" # Qué se ejecutó tipo: RunTipo metodo: str parametros: dict # Ejemplos: # {"col": "ingreso", "where": "edad>=18"} # {"y": "wage", "x": ["educ", "exp"], "se": "HC3"} # {"treatment": "treat", "time": "year", "unit": "id"} # Cómo se ejecutó (SQL-first) motor: str # "duckdb" sql: str # SQL exacto (o SQL principal + SQL auxiliares si aplica) # Auditoría ejecutado_en: "Timestamp" ejecutado_por: str | None`

**Salida del Run**

- No es una nueva versión de datos.

- Su salida son **Artifacts** (tablas, gráficos, reportes) y/o valores guardados como artefactos.

---

## 4) Por qué separarlos (beneficios reales)

**Claros y operativos**

- **Claridad conceptual**: preparar datos ≠ analizar datos.

- **Reproducibilidad fuerte**:
  
  - Operation deja trazado el linaje de datos (versionado).
  
  - Run deja trazado el cálculo (SQL + parámetros).

- **Reutilización**:
  
  - una misma Operation puede aplicarse a distintas versiones/datasets (si schema compatible).
  
  - un mismo Run puede ejecutarse sobre diferentes versiones para comparar resultados.

**Entidades que se reutilizan**

`# Reutilización de Operation: # - misma "recodificación" aplicada sobre versiones distintas # Reutilización de Run: # - mismo modelo (OLS) sobre v2 vs v3 para comparar impacto de limpieza/winsorize`

---

## 5) Flujo correcto del sistema (pipeline)

**Regla de flujo**

`Dataset → DatasetVersion → Operation → DatasetVersion → Run → Artifact`

**Ejemplo completo con entidades**

`# Dataset lógico Dataset(id="hogares_2023", nombre="Encuesta Hogares 2023", descripcion=None, creado_en=...) # v1: importación DatasetVersion(id="dv1", dataset_id="hogares_2023", numero_version=1, version_padre_id=None, ruta_parquet=".../v1/data.parquet", cantidad_filas=..., cantidad_columnas=..., ...) # Operation: filtrar Operation(id="op1", tipo="filtrar", parametros={"where": "edad >= 18"}, version_entrada_id="dv1", version_salida_id="dv2", ...) # v2: resultado del filtro DatasetVersion(id="dv2", dataset_id="hogares_2023", numero_version=2, version_padre_id="dv1", ruta_parquet=".../v2/data.parquet", ...) # Run: media Run(id="run1", dataset_version_id="dv2", tipo="descriptivo", metodo="media", parametros={"col": "ingreso"}, motor="duckdb", sql="SELECT AVG(ingreso) ...", ...) # Artifact: tabla o reporte Artifact(id="a1", run_id="run1", tipo="tabla", formato="xlsx", ruta_archivo=".../a1.xlsx", ...)`

---

## 6) Respuesta directa (sin ambigüedad)

- **Run es inmutable** y genera **Artifacts**.

- **Operation es inmutable** y genera **DatasetVersions**.

**Meta-Python (idea normativa)**

`# Prohibición explícita (regla de diseño): # - Operation NO puede crear artifacts. # - Run NO puede crear nuevas DatasetVersion. class Operation: # output_version_id obligatorio version_salida_id: "DatasetVersionID" class Run: # no tiene output_version_id dataset_version_id: "DatasetVersionID"`

---

## 7) Regla final (para documentar en el repo)

**Regla**

`Operations transforman datos y crean DatasetVersions. Runs analizan datos y crean Artifacts. Ningún componente hace ambas cosas.`

**Invariantes formales (para validar en core/DB)**

`# Invariantes conceptuales # 1) Operation siempre produce una versión de salida assert Operation.version_salida_id is not None # 2) Operation tiene entrada salvo que sea importación if Operation.tipo != "importar": assert Operation.version_entrada_id is not None # 3) Run siempre referencia una versión existente assert Run.dataset_version_id is not None # 4) Run siempre registra SQL ejecutado assert Run.sql is not None # 5) Artifact siempre referencia un Run assert Artifact.run_id is not None`
