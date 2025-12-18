# 📦 Proyecto SARA — Diseño Técnico de Datasets

Este documento describe el **modelo técnico de datasets** utilizado en el proyecto **SARA**.  
El diseño prioriza **reproducibilidad**, **escalabilidad**, **auditabilidad** y **uso académico/profesional**.

---

## 1. Principios de diseño

- Los datos **no se editan en lugar** (inmutabilidad)
- Cada transformación genera una **nueva versión**
- Los datos “pesados” viven en **Parquet**
- La base relacional guarda **solo metadatos**
- Todo análisis referencia explícitamente una **versión de dataset**

Este esquema permite:
- reproducir resultados
- auditar procesos
- escalar a millones de filas
- evitar errores conceptuales en análisis

---

## 2. Entidades principales

### 2.1 Dataset
Representa una **fuente lógica de datos**.

Ejemplos:
- Encuesta de hogares 2023
- Datos administrativos FCE
- Dataset simulado para docencia

**Campos típicos**
- `id`
- `name`
- `description`
- `owner / project / course`
- `created_at`

Un `Dataset` **no contiene datos**, solo contexto.

---

### 2.2 DatasetVersion (entidad clave)
Cada modificación crea una **nueva versión inmutable** del dataset.

Ejemplos:
- v1: datos originales importados
- v2: filtro `edad >= 18`
- v3: recodificación de variables
- v4: selección de columnas

**Campos**
- `id`
- `dataset_id`
- `version_number`
- `parent_version_id` (opcional)
- `parquet_path`
- `row_count`
- `column_count`
- `created_at`
- `created_by`

Nunca se modifica una versión existente.

---

## 3. Almacenamiento físico de datos

### 3.1 Parquet (datos)
Cada versión apunta a un archivo Parquet:

datasets/{dataset_id}/v{version_number}/data.parquet


Motivos:
- formato columnar
- lectura selectiva de columnas
- compresión eficiente
- interoperable (Python, R, Julia, DuckDB)

---

### 3.2 PostgreSQL (metadatos)
En PostgreSQL se almacenan:
- datasets
- versiones
- columnas
- operaciones
- corridas de análisis

**Nunca** datos tabulares grandes.

---

## 4. Columnas y metadatos

### 4.1 DatasetColumn
Describe cada columna **por versión** del dataset.

**Campos relevantes**
- `dataset_version_id`
- `name`
- `dtype` (int, float, category, string, date)
- `role`:
  - outcome
  - predictor
  - id
  - time
  - weight
- `n_unique`
- `missing_pct`
- `min_value`
- `max_value`
- `description` (opcional)

Esto habilita:
- validaciones automáticas
- UX guiada
- plantillas de modelos

---

## 5. Operaciones sobre datasets

### 5.1 Operation
Una `Operation` representa una transformación declarativa.

Ejemplos:
- Filtro (`edad >= 18`)
- Selección de columnas
- Recodificación
- Agrupación simple

**Campos**
- `operation_type`
- `parameters_json`
- `input_version_id`
- `output_version_id`
- `created_at`

Las operaciones construyen el **linaje del dataset**.

---

## 6. Preview y perfilado

Para cada `DatasetVersion`:
- preview limitado (ej. 100 filas)
- perfil automático de columnas:
  - tipo
  - porcentaje de missing
  - cardinalidad
  - rangos numéricos

Estos cálculos se realizan con **DuckDB**, no cargando todo en memoria.

---

## 7. Relación con análisis y modelos

Todo análisis (estadística o econometría):
- referencia explícitamente un `dataset_version_id`
- nunca trabaja sobre “el dataset en general”

Esto garantiza:
- reproducibilidad
- coherencia de resultados
- comparación entre corridas

---

## 8. Ventajas del diseño

### Técnicas
- Escala a millones de filas
- Bajo uso de RAM
- Separación clara entre datos y metadatos

### Académicas / profesionales
- Reproducibilidad estructural
- Auditoría completa
- Claridad metodológica

---

## 9. Resumen conceptual

Dataset
└── DatasetVersion (Parquet)
├── DatasetColumn (metadatos)
├── Operation (linaje)
└── Analysis / Run (resultados)


Este modelo es la base sobre la cual se construyen:
- estadística descriptiva
- inferencia
- econometría aplicada
- causalidad
- notebooks (futuro)

---

## 10. Alcance

Este diseño cubre:
- docencia universitaria
- investigación aplicada
- consultoría profesional

No apunta a big data extremo (cientos de millones) como objetivo primario.
