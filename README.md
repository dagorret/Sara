🇪🇸 Español | [🇬🇧 English](README_EN.md)

# SARA

## Plataforma de análisis estadístico y econométrico con reproducibilidad

![Python](https://img.shields.io/badge/Python-3.12-blue)
![DuckDB](https://img.shields.io/badge/DuckDB-Analytical%20DB-orange)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![License](https://img.shields.io/badge/License-Citation--Required-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Linux-blue)

---

## ⚡ Quick Start

```bash
git clone https://github.com/tu_usuario/sara.git
cd sara
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m desktop_app.main
```

---

## ✨ Características principales

* Modelos econométricos: OLS, Logit, Probit
* Base analítica con DuckDB
* UI interactiva tipo **Stata moderno**
* Reportes automáticos (interpretativos y técnicos)
* Reproducibilidad del análisis
* CLI + Desktop

---

# 🧠 ¿Qué es SARA?

SARA es una plataforma académica para:

* análisis estadístico interactivo
* econometría aplicada
* generación de reportes
* reproducibilidad científica

> Cada resultado puede reconstruirse a partir del dataset y las decisiones analíticas.

---

# ⚙️ Tecnologías

### Core

* Python 3.12
* DuckDB
* Pandas / NumPy
* Statsmodels

### UI

* PySide6 (Qt)
* Arquitectura desacoplada

---

# 🚀 Uso

## CLI

```bash
python src/cli.py --method ols --file datos/ejemplo.csv --y ingreso --x educacion experiencia
```

## Desktop

* cargar dataset
* aplicar filtros
* seleccionar variables
* ejecutar modelos
* ver resultados en tabs

> Se incluyen datasets en `datos/` para pruebas rápidas.

---

# 🐧 Instalación en Linux

```bash
git clone https://github.com/tu_usuario/sara.git
cd sara
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m desktop_app.main
```

---

# 📁 Estructura

```
src/core/        → motor analítico
desktop_app/     → interfaz gráfica
datos/           → datasets
resultados/      → outputs
data/            → DuckDB (sara.db)
tests/           → tests
```

---

# 💾 Persistencia

DuckDB (`data/sara.db`) almacena:

* datasets
* estados
* resultados

---

# 🔮 Futuro

* Windows (.exe)
* macOS (.app)

---

# 📜 Licencia

> Uso libre con atribución obligatoria.
> Cualquier uso, modificación o distribución debe citar la fuente original.

---

# 👨‍💻 Autor

**Carlos Dagorret**

---

# 💬 Conclusión

SARA es un sistema para analizar, interpretar y reproducir resultados de forma clara y rigurosa.
