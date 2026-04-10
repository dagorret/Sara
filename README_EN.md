[🇪🇸 Versión en Español](README.md)

# SARA

## Statistical and Econometric Analysis Platform with Reproducibility

![Python](https://img.shields.io/badge/Python-3.12-blue)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20DB-orange)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![License](https://img.shields.io/badge/License-Citation--Required-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)

---

## ⚡ Quick Start

```bash
git clone https://github.com/your_user/sara.git
cd sara
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m desktop_app.main
```

---

## ✨ Key Features

* Econometric models: OLS, Logit, Probit
* Analytical backend with DuckDB
* Interactive UI (modern Stata-style)
* Automatic reporting (technical + interpretative)
* Reproducible analysis
* CLI + Desktop

---

# 🧠 What is SARA?

SARA is an academic platform for:

* interactive statistical analysis
* applied econometrics
* report generation
* scientific reproducibility

> Every result can be reconstructed from the dataset and analytical decisions.

---

# ⚙️ Technologies

### Core

* Python 3.12
* DuckDB
* Pandas / NumPy
* Statsmodels

### UI

* PySide6 (Qt)
* Decoupled architecture

---

# 🚀 Usage

## CLI

```bash
python src/cli.py --method ols --file datos/ejemplo.csv --y ingreso --x educacion experiencia
```

## Desktop

* load dataset
* apply filters
* select variables
* run models
* view results

> Sample datasets available in `datos/`.

---

# 🐧 Installation (Linux)

```bash
git clone https://github.com/your_user/sara.git
cd sara
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m desktop_app.main
```

---

# 📁 Structure

```
src/core/        → analytical engine
desktop_app/     → UI
datos/           → datasets
resultados/      → outputs
data/            → DuckDB (sara.db)
tests/           → tests
```

---

# 💾 Persistence

DuckDB (`data/sara.db`) stores:

* datasets
* analysis states
* results

---

# 🔮 Future

* Windows (.exe)
* macOS (.app)

---

# 📜 License

> Free to use with attribution.
> Any use, modification, or distribution must cite the original source.

---

# 👨‍💻 Author

**Carlos Dagorret**

---

# 💬 Final Note

SARA is a system designed to analyze, interpret, and reproduce results in a clear and structured way.
