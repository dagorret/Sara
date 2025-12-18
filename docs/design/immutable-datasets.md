## ⚙️ Design decision: Why immutable datasets

SARA enforces **immutable datasets**: once a dataset version is created, it is never modified.
All transformations generate **new dataset versions**.

This section explains why immutability is a core architectural decision.

---

### Problem to solve

In academic and professional analysis, data workflows often suffer from:

- silent data modifications,
- unclear preprocessing steps,
- irreproducible results,
- ambiguity about which data was actually analyzed.

Mutable datasets make it impossible to reliably answer a simple question:

> *“Which exact data produced this result?”*

---

### What immutability means in SARA

- Dataset files are **never edited in place**.
- Every transformation (filtering, recoding, winsorization, discretization) produces:
  - a **new dataset version**,
  - stored as a new Parquet file.
- Each analysis explicitly references a **dataset version ID**.

There is no concept of “current data” without a version.

---

### Dataset versioning model

```
Dataset
  └── DatasetVersion v1  (raw import)
  └── DatasetVersion v2  (filter: age >= 18)
  └── DatasetVersion v3  (winsorize income)
```
Each version:
- is immutable,
- has a clear lineage,
- can be reused independently.

---

### Why immutability is essential

#### 1. Reproducibility by construction

Immutability guarantees that:
- the same dataset version always produces the same results,
- analyses can be rerun months or years later,
- results can be verified independently.

Reproducibility is not an afterthought — it is enforced structurally.

---

#### 2. Full auditability

Every dataset version has:
- a parent version,
- a recorded operation,
- explicit parameters.

This makes it possible to:
- inspect the full data lineage,
- understand every preprocessing step,
- explain results in academic or institutional settings.

---

#### 3. Error prevention

Immutability prevents:
- accidental overwrites,
- irreversible cleaning steps,
- confusion between exploratory and final datasets.

Users can:
- experiment freely,
- branch versions,
- always return to earlier states.

---

#### 4. Alignment with analytical workflows

Statistical and econometric workflows are naturally **batch-oriented**:

- data is prepared,
- analysis is run,
- results are generated.

They do not require row-by-row updates.

Immutable datasets align perfectly with:
- Parquet storage,
- DuckDB analytical queries,
- versioned analysis runs.

---

#### 5. Pedagogical clarity

In teaching contexts, immutability allows instructors and students to:

- distinguish raw data from processed data,
- understand the impact of each transformation,
- avoid “black box” preprocessing.

This improves methodological understanding, not just technical execution.

---

### What immutability does NOT mean

- It does **not** mean data cannot be transformed.
- It does **not** mean data exploration is restricted.
- It does **not** mean duplication of large datasets in memory.

It simply means:
> *Transformations are explicit, versioned, and traceable.*

---

### Comparison with mutable approaches

| Mutable datasets | Immutable datasets (SARA) |
|------------------|---------------------------|
| Silent changes   | Explicit operations       |
| Hard to reproduce| Reproducible by design    |
| Risky cleanup    | Safe experimentation      |
| Unclear lineage  | Full data provenance      |

---

### Academic justification

Immutability is a standard principle in:
- reproducible research,
- data provenance systems,
- modern analytical architectures.

It is widely adopted in:
- scientific data pipelines,
- versioned data lakes,
- analytical databases.

SARA applies this principle at an academic and institutional scale.

---

### Conclusion

SARA uses immutable datasets because they:

- guarantee reproducibility,
- enable full auditability,
- prevent accidental data corruption,
- align with analytical (not transactional) workflows,
- improve pedagogical clarity.

Immutable datasets are not a limitation — they are the foundation of reliable statistical and econometric analysis in SARA.

