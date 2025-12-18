# 🧪 Minimal Working Example (MWE)
## CSV → Parquet → DuckDB → Mean → Winsorize → New Version

This document demonstrates the **core SARA workflow** end-to-end:

1) ingest a CSV dataset  
2) store it as an immutable **Parquet** dataset version  
3) compute a descriptive statistic (**mean**) using **DuckDB**  
4) apply a transformation (**winsorization**) as a recorded operation  
5) write a **new Parquet dataset version** (no in-place edits)

---

## 0) Assumptions

- You have Python installed.
- You can install packages:
  - `duckdb`
  - `pyarrow` (for Parquet writing via DuckDB)
- Input file: `data/raw/example.csv`

Example CSV columns:
- `id` (int)
- `age` (int)
- `income` (float)

---

## 1) Folder layout (suggested)

data/ raw/ example.csv datasets/ <dataset_id>/ v1/ data.parquet v2/ data.parquet

In SARA:
- Parquet is the **data source of truth**
- metadata (dataset/version/run) would live in PostgreSQL (not shown here)

---

## 2) Install dependencies

```bash
pip install duckdb pyarrow


---

3) Convert CSV → Parquet (create DatasetVersion v1)

import os
import duckdb

DATASET_ID = "example_dataset"
V1_PATH = f"data/datasets/{DATASET_ID}/v1"
os.makedirs(V1_PATH, exist_ok=True)

csv_path = "data/raw/example.csv"
parquet_v1 = f"{V1_PATH}/data.parquet"

con = duckdb.connect()

# DuckDB reads the CSV and writes a Parquet file (version v1)
con.execute(f"""
    COPY (
        SELECT *
        FROM read_csv_auto('{csv_path}')
    )
    TO '{parquet_v1}'
    (FORMAT PARQUET);
""")

print("Created v1:", parquet_v1)
```
Outcome:

v1/data.parquet becomes the immutable dataset version.



---

## 4) Compute mean using DuckDB (no pandas, no full RAM load)

```
import duckdb

DATASET_ID = "example_dataset"
parquet_v1 = f"data/datasets/{DATASET_ID}/v1/data.parquet"

con = duckdb.connect()

mean_income = con.execute(f"""
    SELECT AVG(income) AS mean_income
    FROM read_parquet('{parquet_v1}')
""").fetchone()[0]

print("Mean income (v1):", mean_income)
```

This scales because DuckDB:

reads only the required column,

processes data in chunks,

avoids loading the full dataset into memory.



---

## 5) Winsorize a column (create DatasetVersion v2)

Winsorization requires:

1. compute percentile limits (e.g., 1% and 99%)


2. clamp values to those limits


3. write a new Parquet version (v2)


```
import os
import duckdb

DATASET_ID = "example_dataset"
V1 = f"data/datasets/{DATASET_ID}/v1/data.parquet"
V2_PATH = f"data/datasets/{DATASET_ID}/v2"
os.makedirs(V2_PATH, exist_ok=True)

V2 = f"{V2_PATH}/data.parquet"

p_low = 0.01
p_high = 0.99

con = duckdb.connect()

# 1) compute winsor limits
lo, hi = con.execute(f"""
    SELECT
      quantile_cont(income, {p_low}) AS lo,
      quantile_cont(income, {p_high}) AS hi
    FROM read_parquet('{V1}')
""").fetchone()

# 2) write v2 with winsorized income
con.execute(f"""
    COPY (
        WITH limits AS (SELECT {lo}::DOUBLE AS lo, {hi}::DOUBLE AS hi)
        SELECT
            *,
            CASE
              WHEN income < (SELECT lo FROM limits) THEN (SELECT lo FROM limits)
              WHEN income > (SELECT hi FROM limits) THEN (SELECT hi FROM limits)
              ELSE income
            END AS income_wins
        FROM read_parquet('{V1}')
    )
    TO '{V2}'
    (FORMAT PARQUET);
""")

print("Created v2:", V2)
print("Winsor limits:", lo, hi)
```

Notes:

v1 is untouched.

v2 is a new immutable dataset version.

income_wins is added as a new column (recommended).

Alternatively, you could replace income in v2, but still as a new version.




---

## 6) Validate the new version

Compute mean on the winsorized column:

```
import duckdb

DATASET_ID = "example_dataset"
parquet_v2 = f"data/datasets/{DATASET_ID}/v2/data.parquet"

con = duckdb.connect()

mean_income_w = con.execute(f"""
    SELECT AVG(income_wins) AS mean_income_wins
    FROM read_parquet('{parquet_v2}')
""").fetchone()[0]

print("Mean income (winsorized, v2):", mean_income_w)
```


---

## 7) How this maps to SARA concepts

In the full platform, these steps correspond to:

Dataset: logical source (example_dataset)

DatasetVersion v1: import result (raw snapshot)

Operation: winsorize(income, p_low=0.01, p_high=0.99)

DatasetVersion v2: output snapshot after operation

Run: mean calculation linked to a specific dataset version

Artifact: optional exports (tables/plots)


Key rule:

> No in-place edits. Everything is versioned.




---

## 8) Next steps

To turn this into the SARA core:

persist metadata in PostgreSQL (datasets, dataset_versions, operations, runs)

implement typed operation registry:

mean(...)

winsorize(...)

discretize(...)


add UI actions:

preview (LIMIT 100)

filters + counts

create new version




---
