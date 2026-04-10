[🇪🇸 Versión en Español](README.md)
# SARA

## Academic System for Reproducibility and Analysis

SARA is an academic platform focused on **statistical analysis**, **applied econometrics**, and **scientific reproducibility**, designed for **university teaching**, **research**, and **professional analytical work**.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20DB-orange)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![License](https://img.shields.io/badge/License-Citation--Required-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)

---

# 🧠 What is SARA?

SARA is a tool that allows users to:

* analyze datasets interactively
* apply econometric models (OLS, Logit, Probit)
* evaluate results using statistical metrics
* generate automatic, interpretable reports
* reproduce complete analyses from their analytical state

The system is built around the principle of:

> **analytical reproducibility**, where every result can be reconstructed from the dataset and the analytical decisions made.

---

# ⚙️ Technologies

### 🔹 Analytical Core

* **Python 3.12**
* **DuckDB** (embedded analytical database)
* **Pandas / NumPy**
* **Statsmodels**

---

### 🔹 User Interface

* **PySide6 (Qt)**
* Decoupled architecture (core independent from UI)

---

### 🔹 Additional Components

* Robust data validation
* Logging system
* Automatic report generation
* CLI support

---

# 📊 Theoretical Foundations

SARA is based on:

### 🔹 Statistics

* statistical inference
* parameter estimation
* hypothesis testing

---

### 🔹 Econometrics

* linear regression (OLS)
* binary choice models:

  * Logit
  * Probit

---

### 🔹 Data Science

* exploratory analysis
* model evaluation (R², AUC, accuracy)
* data validation

---

### 🔹 Scientific Reproducibility

* separation between data and analytical state
* persistent configurations
* reproducible model execution

---

# 🚀 Usage

SARA can be used in two ways:

---

## 🔹 1. Command Line Interface (CLI)

Run analyses directly from the terminal.

### OLS example:

```bash
python src/cli.py --method ols --file datos/ejemplo.csv --y ingreso --x educacion experiencia
```

---

### Logit example:

```bash
python src/cli.py --method logit --file datos/logit_grande.csv --y aprobado --x horas_estudio asistencia --threshold 0.5
```

---

## 🔹 2. Desktop Application

Graphical interface that allows users to:

1. load datasets
2. apply filters
3. select variables
4. run models
5. visualize results in real time

Includes:

* control panel
* data table
* results panel with tabs
* automatic reports

---

# 🐧 Installation (Linux)

## 🔹 1. Clone repository

```bash
git clone https://github.com/your_user/sara.git
cd sara
```

---

## 🔹 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 🔹 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔹 4. Run desktop app

```bash
python -m desktop_app.main
```

---

## 🔹 5. Run CLI

```bash
python src/cli.py --help
```

---

# 📁 Project Structure

```text
src/core/        → analytical engine
desktop_app/     → graphical interface
datos/           → sample datasets
resultados/      → generated outputs
data/            → DuckDB database (sara.db)
tests/           → test suite
```

---

# 💾 Persistence

SARA uses **DuckDB** (`data/sara.db`) as a local database to store:

* datasets
* analysis states
* intermediate results

---

# 🔮 Future Development

Currently, SARA is available for **Linux**.

Planned support includes:

* 🟦 Windows (.exe)
* 🍎 macOS (.app)

via cross-platform packaging.

---

# 🎯 Project Goal

SARA aims to bridge the gap between:

* traditional academic tools
* modern analytical environments

by providing a system that is:

* accessible
* reproducible
* extensible

---

# 📜 License

This project is free to use under the following condition:

> **Use, modification, and distribution are allowed provided that the original source is properly cited.**

---

# 👨‍💻 Author

**Carlos Dagorret**

---

# 💬 Final Note

SARA is not just a computational tool:

> it is a system designed to analyze, interpret, and reproduce results in a clear, structured, and academically rigorous way.
