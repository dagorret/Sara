# SARA  
## Sistema Académico de Reproducibilidad y Análisis

SARA es una plataforma académica orientada a **estadística**, **econometría aplicada** y **reproducibilidad científica**, diseñada para docencia universitaria, investigación y uso profesional.

El proyecto prioriza:
- claridad metodológica  
- reproducibilidad estructural  
- escalabilidad razonable  
- una UX guiada y moderna  

---

## 🎯 Objetivos del proyecto

- Facilitar el uso real de estadística y econometría que hoy está en los programas, pero no se aplica por barreras técnicas.
- Unificar docencia, investigación y análisis profesional en una sola herramienta.
- Garantizar que **todo resultado sea reproducible**, auditable y versionado.
- Ofrecer una alternativa moderna a flujos basados exclusivamente en scripts.

---

## 🧠 Principios de diseño

- Los datos **no se editan en lugar** (inmutabilidad).
- Cada transformación genera una **nueva versión del dataset**.
- Los datos tabulares viven en **Parquet**.
- La base relacional almacena **solo metadatos**.
- Todo análisis referencia explícitamente una **versión del dataset**.

Este enfoque permite:
- reproducir resultados,
- auditar procesos,
- escalar a millones de filas,
- evitar errores conceptuales frecuentes en análisis estadístico.

---

## 📦 Modelo de datos (resumen)

Dataset └── DatasetVersion (Parquet) 
        ├── DatasetColumn (metadatos) 
        ├── Operation (linaje) 
        └── Run / Analysis (resultados)

        - **Dataset**: fuente lógica (encuesta, base administrativa, simulación).
- **DatasetVersion**: snapshot inmutable de los datos.
- **Operation**: transformación declarativa (filtros, recodificaciones, winsorización).
- **Run**: ejecución de estadística o modelo sobre una versión específica.

---

## 🗂️ Almacenamiento

### Datos
- **Parquet** (columnar, eficiente, interoperable).
- Cada versión se guarda como un archivo independiente.

### Metadatos
- **PostgreSQL**
- Datasets, versiones, columnas, operaciones y corridas.

---

## ⚙️ Motor analítico: DuckDB

SARA utiliza **DuckDB** como motor analítico embebido.

### ¿Por qué DuckDB?
- Lectura directa de Parquet.
- Operaciones SQL analíticas eficientes.
- No requiere servidor.
- Bajo consumo de memoria.
- Funciona igual en Windows, Linux y macOS.

DuckDB se usa para:
- estadística descriptiva (`AVG`, `COUNT`, `STDDEV`, `quantile_cont`, etc.),
- filtros y agregaciones,
- generación de nuevas versiones de datasets,
- previews y perfilado de columnas.

### Referencias
- Sitio oficial: https://duckdb.org  
- Documentación: https://duckdb.org/docs/  
- Paper:  
  Raasveldt, M., & Mühleisen, H. (2019).  
  *DuckDB: an Embeddable Analytical Database*. arXiv:1909.08833

---

## 📊 Módulos principales (estado inicial)

### Dataset
- Importación (CSV, Excel)
- Versionado inmutable
- Perfilado de columnas
- Preview controlado (hasta 100 filas)

### Estadística descriptiva
- Media, mediana, varianza, desvío
- Tablas de frecuencia
- Histogramas y gráficos básicos

### Transformaciones
- Filtros
- Recodificaciones
- Winsorización
- Discretización

Cada transformación genera una **nueva versión del dataset**.

---

## 🔁 Reproducibilidad

Cada análisis:
- referencia una versión concreta del dataset,
- registra parámetros,
- guarda resultados y artefactos,
- puede reproducirse en cualquier momento.

No existen:
- ediciones manuales de celdas,
- cambios silenciosos,
- resultados sin contexto.

---

## 🚧 Alcance actual

SARA está pensado para:
- docencia universitaria,
- investigación aplicada,
- análisis profesional (policy, consultoría).

No apunta inicialmente a big data extremo (cientos de millones de filas), sino a un rango típico académico/profesional.

---

## 🧭 Estado del proyecto

SARA se encuentra en desarrollo activo, comenzando por:
- core de datasets,
- estadística descriptiva,
- arquitectura reproducible.

La econometría avanzada y la integración con notebooks e IA forman parte del roadmap futuro.

---

## 📜 Licencia
(Definir)

---

## 🏫 Contexto institucional
Proyecto desarrollado en ámbito universitario, con foco en enseñanza, investigación y transferencia.

---
