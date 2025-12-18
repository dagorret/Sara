## ⚙️ Design decision: Why SQL-first analytics

SARA adopts a **SQL-first analytics** approach:  
all core analytical operations are expressed, executed, and logged as SQL queries.

This document explains why SQL is the primary analytical language in SARA.

---

### Problem to solve

Many analytical systems rely on:
- opaque code execution,
- hidden transformations,
- stateful, imperative scripts,
- results that are difficult to audit or explain.

In academic and institutional contexts, this creates serious issues:
- lack of transparency,
- poor reproducibility,
- difficulty in teaching and reviewing analytical steps.

---

### What SQL-first means in SARA

- All core operations are expressed as SQL:
  - filtering
  - aggregation
  - transformation
  - statistical summaries
- SQL queries are:
  - generated programmatically,
  - executed by DuckDB,
  - logged as part of each analysis run.
- SQL is the **source of truth** for analytical logic.

Python is used to:
- orchestrate execution,
- validate parameters,
- manage versions and metadata,
- never to hide analytical logic.

---

### Why SQL is the right abstraction

#### 1. Transparency and auditability

SQL queries are:
- explicit,
- human-readable,
- inspectable after execution.

Any result in SARA can be traced back to:
- the dataset version,
- the exact SQL query that produced it.

This enables:
- peer review,
- institutional audits,
- methodological validation.

---

#### 2. Pedagogical value

SQL is:
- widely taught and understood,
- conceptually close to relational algebra,
- easier to explain than imperative data manipulation.

Using SQL allows instructors and students to:
- see each analytical step clearly,
- understand how results are produced,
- connect theory with implementation.

This directly supports SARA’s teaching objectives.

---

#### 3. Declarative, not imperative

SQL is **declarative**:
- users specify *what* they want,
- not *how* to compute it.

This:
- reduces accidental complexity,
- avoids hidden state,
- aligns with reproducible workflows.

Declarative transformations are easier to version, compare, and reason about.

---

#### 4. Engine independence (future-proofing)

By expressing analytics in SQL:
- analytical logic is decoupled from the UI,
- execution can evolve independently,
- alternative engines can be evaluated in the future.

DuckDB is the current execution engine, but SQL keeps the system flexible.

---

#### 5. Alignment with analytical workloads

Statistical and econometric workflows are naturally expressed as:
- filters,
- aggregations,
- joins,
- window functions.

SQL is a natural and efficient language for these operations, especially when combined with columnar storage (Parquet).

---

### Why not Python-first or notebook-first analytics?

Imperative, script-based workflows introduce several risks:

| Python-first / notebooks | Impact on SARA |
|--------------------------|----------------|
| Hidden mutable state     | Weak reproducibility |
| Order-dependent execution| Hard to audit |
| Difficult to version     | Conceptual confusion |
| Poor teaching clarity   | Reduced pedagogical value |

Notebooks remain valuable for:
- exploration,
- advanced research,
- experimentation.

However, they are intentionally **not the core abstraction** in SARA.

---

### How SQL-first integrates with UX

In SARA:
- users interact through forms, wizards, and parameters,
- the system generates SQL queries transparently,
- queries can be:
  - logged,
  - displayed,
  - exported.

The user benefits from SQL’s rigor without needing to write SQL manually.

---

### What SQL-first does NOT imply

- Users are **not required** to write SQL.
- SARA is **not** a database administration tool.
- SQL is an internal, transparent representation of analytical logic.

The UI remains user-friendly and guided.

---

### Academic justification

SQL-first approaches are standard in:
- analytical databases,
- data provenance systems,
- reproducible research platforms.

They balance:
- expressiveness,
- transparency,
- long-term maintainability.

This makes SQL-first analytics suitable for institutional and academic adoption.

---

### Conclusion

SARA adopts a SQL-first analytics approach because it:

- guarantees transparency and auditability,
- enforces declarative, reproducible workflows,
- supports teaching and methodological clarity,
- decouples analytical logic from UI and orchestration,
- aligns naturally with statistical and econometric analysis.

SQL-first analytics is not a technical preference — it is a foundational design choice for reliable, reproducible analysis in SARA.
