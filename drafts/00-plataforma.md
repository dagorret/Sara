# Plataforma de Computación Científica  
## Resumen integral del diseño y la discusión

---

## 1. Objetivo general

Diseñar una **plataforma de computación científica reproducible**, con **interfaz gráfica tipo “un click”**, usable tanto en **web como en escritorio**.

El dominio inicial es **microeconometría**, pero la arquitectura está pensada desde el inicio para ser **multidisciplinaria**, aplicable también a:
- Física
- Climatología
- Microbiología
- Medicina / Epidemiología

---

## 2. Principios fundamentales

- Separación estricta entre:
  - **Datos**
  - **Metadatos**
  - **Cálculo científico**
- **Reproducibilidad científica** (versionado de datos y modelos)
- **Escalabilidad** desde 10K filas hasta millones
- **UX guiada**: primero se elige el modelo, luego los datos y parámetros
- **Motor numérico propio en Python**
- Mismo concepto para **web y escritorio**

---

## 3. Arquitectura óptima final

### 3.1 Datos
- **Parquet** como formato principal:
  - Columnar
  - Comprimido
  - Tipado
  - Lectura selectiva de columnas
- Los datos son **inmutables por versión**

Estructura típica:

datasets/ dataset_id/ v1/ data.parquet v2/ data.parquet

### 3.2 Motor analítico
- **DuckDB**
  - Motor analítico embebido
  - Lee Parquet directamente
  - Permite SQL para filtros y joins
  - Ideal para millones de filas
  - Funciona excelente en escritorio y web

### 3.3 Metadatos
- **Web**: PostgreSQL
- **Escritorio**: DuckDB local (archivo)

Tablas conceptuales:
- dataset
- dataset_version
- dataset_column
- model_run

---

## 4. Modelo de datos

### Dataset
Entidad lógica que representa una fuente de datos.

### Dataset version
Cada cambio relevante crea una nueva versión.
Cada versión apunta a un Parquet específico.

### Dataset column
Describe las variables:
- nombre
- tipo (`dtype`)
- rol sugerido (`target`, `feature`, `id`, `time`)

### Tabla ancha (wide table)
- 1 versión de dataset = 1 tabla lógica
- 1 fila = 1 observación
- 1 columna = 1 variable
- **No usar EAV** para datos científicos

---

## 5. Importación y exportación

### Importación
- CSV
- Excel
- Conversión automática a Parquet
- Perfilado de columnas (dtype, missing, min/max, etc.)

### Exportación
- CSV
- Excel
- HTML
- PDF / Word en versiones posteriores

---

## 6. Computación científica

### Stack base
- **NumPy**: álgebra lineal
- **SciPy**: optimización, estadística, ODE
- **DuckDB**: preparación eficiente de datos

### Principios numéricos
- No invertir matrices directamente
- Usar QR, Cholesky o SVD
- **Cálculo por bloques (streaming)** para millones
- Control de estabilidad numérica y memoria

---

## 7. Microeconometría (dominio inicial)

Familias de modelos previstas:
- OLS / WLS
- Logit / Probit / Multinomial
- Conteo (Poisson, Binomial Negativa)
- Tobit / Heckman
- Panel (FE, RE, GMM)
- IV / 2SLS / GMM
- DID / Event Study / RDD
- Survival
- Modelos estructurales

---

## 8. UX “un click”

Flujo estándar:
1. Elegir modelo
2. Seleccionar variables válidas
3. Configurar opciones
4. Ejecutar
5. Ver resultados y gráficos
6. Exportar
7. Guardar corrida reproducible (`model_run`)

---

## 9. Escalabilidad

- Hasta ~5M filas: Parquet + DuckDB
- 5M–50M: Parquet particionado
- 50M+: streaming y cálculo por bloques
- El admin se usa solo para **gestión**, no para visualizar datos masivos

---

## 10. Multidisciplina

La **misma arquitectura** sirve para:
- Física (ODE, PDE, simulaciones)
- Climatología (grillas, series largas)
- Microbiología (conteo, clustering)
- Medicina / Epidemiología (survival, simulación)

Solo cambia el **core científico**, no la infraestructura.

---

## 11. Comparación con software existente

- MATLAB / Mathematica: motor fuerte, cerrados, caros
- Jupyter: flexible, pero UX basada en código
- Stata / SPSS: UX click, dominio limitado
- Databricks / Palantir: escalan mucho, muy costosos
- KNIME: visual, rígido

No existe una solución abierta que combine todo.

---

## 12. Definición final del proyecto

Plataforma de **computación científica reproducible**,  
**multidisciplinaria**,  
con **UX guiada**,  
basada en estándares modernos (**Parquet, DuckDB, Python**),  
usable tanto en **web como en escritorio**.
