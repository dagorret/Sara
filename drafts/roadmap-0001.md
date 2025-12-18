# 🧭 ROADMAP DEL PRODUCTO
## Plataforma Econométrica Moderna (Web + Desktop)

---

# 🚀 ROADMAP V1 — MVP ACADÉMICO / PROFESIONAL
**Objetivo:**  
Producto **usable desde el día 1** para enseñanza, investigación aplicada y consultoría.  
Enfocado en **UX guiada**, **rigor académico** y **reproducibilidad**.

---

## 🎯 Público objetivo
- Docencia universitaria
- Investigadores académicos
- Consultores y staff técnico (WB, IMF, BCRA, ministerios)

---

## 🧱 Arquitectura base
- Parquet (datos inmutables, versionados)
- DuckDB (consulta y agregaciones)
- Python (NumPy, SciPy, statsmodels/linearmodels)
- PostgreSQL (metadatos, corridas)
- Web + Desktop (misma lógica)

---

## 🧪 Modelos incluidos (V1)
### Núcleo obligatorio
- OLS / WLS
- Errores robustos (HC0–HC5)
- Errores clusterizados
- Logit / Probit
- Panel FE / RE
- IV (2SLS)
- DID clásico
- DID multi-período básico

---

## 🧭 Plantillas (V1)
- Impacto DID
- IV clásico
- Panel FE / RE
- Logit / Probit

---

## 📊 Outputs académicos
- Tablas estilo Stata
  - coeficientes
  - errores estándar
  - significancia
  - notas automáticas
- Exportación:
  - HTML
  - Excel
  - Word

---

## 📈 Gráficos automáticos
- Marginal effects (Logit/Probit)
- Event study básico (DID)
- RD plot básico (Sharp RDD)

---

## 🧠 UX (V1)
- Modo **Sencillo**
- Modo **Pro**
- Wizard por modelo
- Defaults fuertes
- Validaciones metodológicas básicas

---

## ♻️ Reproducibilidad (V1)
- Dataset versionado
- Transformaciones → nueva versión
- Historial de corridas (`model_run`)
- Botón “Reproducir corrida”

---

## ❌ NO entra en V1
- Notebooks
- IA
- Modelos estructurales
- Big data extremo (>10M)
- GPU / HPC

---

# 🔧 ROADMAP V2 — PROFESIONAL AVANZADO + IA ASISTIDA
**Objetivo:**  
Subir el nivel metodológico y de productividad, sin perder control.

---

## 🧪 Nuevos modelos
- Tobit / Heckman
- Poisson / NegBin / ZI / Hurdle
- Panel dinámico (Arellano–Bond)
- RDD Fuzzy
- Matching (PSM, NN)
- Quantile regression

---

## 📊 Outputs avanzados
- Event study completo
- Placebos automáticos
- Balance checks
- Comparación entre corridas
- Reportes multi-modelo

---

## 🤖 IA (asistente metodológico)
### Qué SÍ hace
- Explicar resultados
- Detectar errores comunes:
  - mala especificación
  - falta de variación
  - instrumentos débiles
- Sugerir tests y checks
- Generar texto académico preliminar

### Qué NO hace
- No estima modelos
- No decide causalidad
- No reemplaza criterio humano

---

## 🧠 UX avanzada
- Modo **Pro** expandido
- Comparación visual de especificaciones
- Historial tipo “laboratorio”

---

## 🔌 Integraciones
- Importación de datos públicos:
  - World Bank
  - OECD
- Exportación a repositorios académicos (OSF)

---

# 🧪 ROADMAP V3 — SUPER PRO / FRONTERA
**Objetivo:**  
Plataforma de **investigación de frontera**, experimental y extensible.

---

## 📓 Notebooks integrados
- Notebook generado desde una corrida
- Código reproducible
- Asociado a dataset + versión
- Guardado como “derivación”

---

## 🧠 Modelos avanzados
- Double Machine Learning (DML)
- Synthetic Control
- Modelos estructurales
- MSM / MPEC
- Dynamic discrete choice (Rust)

---

## ⚙️ Computación avanzada
- Streaming completo
- Paralelización
- Integración con:
  - JAX
  - Numba
  - GPU (cuando aplique)

---

## 🤖 IA avanzada
- Copiloto econométrico contextual
- Explicación de notebooks
- Sugerencias de extensiones
- Documentación automática del proyecto

---

## 🌍 Escalabilidad
- Integración con motores externos:
  - Spark
  - Trino
- Uso en oficinas estadísticas (recortes/muestras)

---

## 🧭 Posicionamiento final
> Plataforma científica moderna que:
> - enseña
> - produce
> - documenta
> - reproduce
> - evoluciona

---

# 🏁 RESUMEN ESTRATÉGICO

| Versión | Rol |
|---|---|
| V1 | Enseña y produce |
| V2 | Asiste y profesionaliza |
| V3 | Explora e innova |

