## ⚙️ Design decision: Why Parquet

SARA uses **Apache Parquet** as its primary data storage format for dataset versions.  
This section explains why Parquet is the correct choice for the platform.

---

### Problem to solve

SARA needs a data format that:

- handles medium to large tabular datasets efficiently,
- supports column-level access,
- minimizes storage and I/O costs,
- integrates naturally with analytical engines,
- remains stable and readable over time,
- is suitable for academic reproducibility.

Traditional formats such as CSV or Excel do not meet these requirements.

---

### Why Parquet fits SARA

#### 1. Columnar storage

Parquet is a **columnar file format**.

This means:
- only required columns are read from disk,
- unnecessary data is never loaded,
- analytical queries are significantly faster.

This is ideal for statistics and econometrics, where:
- only a subset of variables is usually needed,
- wide tables are common.

---

#### 2. Efficient compression and encoding

Parquet applies:
- column-wise compression,
- type-specific encodings.

Benefits:
- smaller file sizes,
- faster disk reads,
- reduced storage footprint.

This is especially important in academic environments with limited resources.

---

#### 3. Designed for analytical workloads

Parquet is optimized for:
- scans,
- aggregations,
- filters,
- analytical queries.

It is **not** designed for row-by-row updates, which aligns perfectly with SARA’s principle of **immutability and versioning**.

---

#### 4. Interoperability and longevity

Parquet is:
- an open standard,
- widely adopted across ecosystems.

It can be read by:
- DuckDB
- Python (Arrow, pandas)
- R
- Julia
- Spark
- many other tools

This guarantees:
- long-term accessibility,
- independence from a single software stack,
- institutional safety.

---

#### 5. Natural fit with versioned datasets

In SARA:
- each dataset version corresponds to one Parquet file,
- versions are immutable,
- transformations produce new Parquet files.

This makes Parquet a natural unit of:
- reproducibility,
- auditability,
- lineage tracking.

---

### Why not CSV?

CSV files are:

- row-oriented,
- inefficient for large datasets,
- slow to parse,
- ambiguous in typing,
- prone to encoding issues.

CSV is suitable only for:
- initial data ingestion,
- human inspection.

In SARA, CSV is converted immediately into Parquet.

---

### Why not Excel?

Excel files:

- are not designed for analytical scalability,
- mix data and presentation,
- have size and row limits,
- are difficult to version and audit.

Excel is treated as an **input/output format**, never as a storage format.

---

### Why not a relational database for data storage?

Storing large datasets directly in PostgreSQL or similar systems would:

- duplicate data,
- increase operational complexity,
- require server management,
- complicate desktop usage.

In SARA, relational databases are reserved **exclusively for metadata**.

---

### Academic justification

Parquet is a standard in scientific and analytical computing:

- widely used in research and industry,
- supported by major analytical engines,
- stable and well-documented.

Its adoption aligns with best practices in reproducible research.

---

### Conclusion

Parquet is used in SARA because it:

- enables efficient column-level access,
- minimizes memory and I/O usage,
- integrates seamlessly with DuckDB,
- supports immutable, versioned datasets,
- ensures long-term reproducibility and interoperability.

Parquet is not chosen for convenience, but because it is the correct storage format for SARA’s analytical architecture.
