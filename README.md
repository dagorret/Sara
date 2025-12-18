![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active%20development-orange)
![Reproducibility](https://img.shields.io/badge/reproducibility-guaranteed-brightgreen)
![Academic](https://img.shields.io/badge/use-academic%20%7C%20research-blueviolet)
![Interface](https://img.shields.io/badge/interface-CLI%20%7C%20Web%20%7C%20Desktop-lightgrey)
![DuckDB](https://img.shields.io/badge/engine-DuckDB-yellow)
![Parquet](https://img.shields.io/badge/storage-Parquet-005571)
![Open%20Science](https://img.shields.io/badge/open-science-success)
![Interfaces](https://img.shields.io/badge/interfaces-CLI%20%7C%20Web%20%7C%20Desktop-lightgrey)
![Core](https://img.shields.io/badge/core-programmatic%20API-lightgrey)



# SARA  
## Academic System for Reproducibility and Analysis

SARA is an academic platform for **statistics**, **applied econometrics**, and **scientific reproducibility**, designed for university teaching, research, and professional analytical work.

The project prioritizes:
- methodological clarity  
- structural reproducibility  
- reasonable scalability  
- a guided and modern user experience  

---

## 🎯 Project goals

- Enable real use of statistics and econometrics that are present in curricula but rarely applied due to technical barriers.
- Unify teaching, research, and professional analysis within a single platform.
- Guarantee that **all results are reproducible**, auditable, and versioned.
- Provide a modern alternative to purely script-based analytical workflows.

---

## 🧠 Design principles

- Data is **never edited in place** (immutability).
- Every transformation produces a **new dataset version**.
- Large tabular data is stored in **Parquet** format.
- The relational database stores **metadata only**.
- Every analysis explicitly references a **dataset version**.

This design enables:
- result reproducibility,
- full auditability,
- scalability to millions of rows,
- avoidance of common conceptual errors in data analysis.

---

## 📦 Data model (overview)

Dataset └── DatasetVersion (Parquet) 
        ├── DatasetColumn (metadata) 
        ├── Operation (lineage) 
        └── Run / Analysis (results)
- **Dataset**: logical data source (survey, administrative data, simulation).
- **DatasetVersion**: immutable snapshot of the data.
- **Operation**: declarative transformation (filters, recoding, winsorization).
- **Run**: execution of statistics or models on a specific dataset version.

---

## 🗂️ Storage

### Data
- **Parquet** (columnar, efficient, interoperable).
- Each dataset version is stored as a separate file.

### Metadata
- **PostgreSQL**
- Datasets, versions, columns, operations, and analysis runs.

---

## ⚙️ Analytical engine: DuckDB

SARA uses **DuckDB** as its embedded analytical engine.

### Why DuckDB?
- Direct querying of Parquet files.
- Efficient analytical SQL operations.
- No server required.
- Low memory footprint.
- Cross-platform (Windows, Linux, macOS).

DuckDB is used for:
- descriptive statistics (`AVG`, `COUNT`, `STDDEV`, `quantile_cont`, etc.),
- filtering and aggregation,
- creation of new dataset versions,
- dataset previews and column profiling.

### References
- Official website: https://duckdb.org  
- Documentation: https://duckdb.org/docs/  
- Paper:  
  Raasveldt, M., & Mühleisen, H. (2019).  
  *DuckDB: an Embeddable Analytical Database*. arXiv:1909.08833

---

## 📊 Core modules (initial scope)

### Dataset
- Import (CSV, Excel)
- Immutable versioning
- Column profiling
- Controlled preview (up to 100 rows)

### Descriptive statistics
- Mean, median, variance, standard deviation
- Frequency tables
- Basic plots and histograms

### Transformations
- Filters
- Recoding
- Winsorization
- Discretization

Each transformation produces a **new dataset version**.

---

## 🔁 Reproducibility

Every analysis:
- references a specific dataset version,
- records parameters,
- stores results and artifacts,
- can be reproduced at any time.

There are no:
- manual cell edits,
- silent data changes,
- results without context.

---

## 🚧 Scope and limitations

SARA is designed for:
- university teaching,
- applied research,
- professional analytical work (policy, consulting).

It does not initially target extreme big data workloads (hundreds of millions of rows), but rather the typical academic and professional scale.

---

## 🧭 Project status

SARA is under active development, currently focusing on:
- dataset core architecture,
- descriptive statistics,
- reproducible analytical workflows.

Advanced econometrics, notebooks, and AI-assisted features are part of the future roadmap.

---

## 📜 License

This project is released under the **MIT License**.
See the [LICENSE](LICENSE) file for details.

If you use SARA in academic work, please cite the project (see `CITATION.cff`).

---

## 🏫 Institutional context

This project is developed in an academic environment, with a focus on teaching, research, and knowledge transfer.

---
        
        
