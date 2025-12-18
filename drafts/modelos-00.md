
# 📌 I. Modelos de Regresión Básicos (base del sistema)

### 1. Modelos Lineales

- Regresión lineal simple (OLS)

- Regresión lineal múltiple

- Regresión ponderada (WLS)

- Regresión con restricciones lineales

- Errores robustos (HC0–HC5)

- Clustering de errores

👉 **Base obligatoria** del sistema

---

# 📌 II. Modelos para Variable Dependiente Limitada

### 2. Modelos Binarios

- Logit

- Probit

- Complementary log-log

- Linear Probability Model (LPM)

### 3. Modelos Multinómicos

- Logit multinomial

- Probit multinomial

- Conditional logit (McFadden)

- Nested logit

- Mixed logit (random parameters)

### 4. Modelos Ordenados

- Logit ordenado

- Probit ordenado

- Generalized ordered models

👉 Usados en **elección discreta**, preferencias, mercado laboral.

---

# 📌 III. Modelos para Datos Censurados y Truncados

### 5. Modelos Tobit y derivados

- Tobit clásico

- Tobit con heterocedasticidad

- Tobit tipo I, II, III

### 6. Selección Muestral

- Modelo de Heckman (dos etapas)

- Heckman ML

- Endogenous switching models

---

# 📌 IV. Modelos de Conteo

### 7. Modelos Poisson y extensiones

- Poisson

- Quasi-Poisson

- Binomial negativa

- Zero-inflated Poisson

- Zero-inflated NB

- Hurdle models

---

# 📌 V. Modelos de Datos de Panel (MUY CLAVE)

### 8. Panel Estático

- Pooled OLS

- Efectos fijos (FE)

- Efectos aleatorios (RE)

- FE con variables instrumentales

- Test Hausman

### 9. Panel Dinámico

- Arellano–Bond

- Arellano–Bover / Blundell–Bond (System GMM)

- Difference GMM

- Bias-corrected FE

👉 Núcleo de **microeconometría moderna**

---

# 📌 VI. Endogeneidad e Instrumentos

### 10. Variables Instrumentales

- IV (2SLS)

- LIML

- GMM

- Weak instruments diagnostics

- Overidentification tests (Sargan, Hansen)

---

# 📌 VII. Evaluación de Impacto y Causalidad

### 11. Modelos Causales

- Difference-in-Differences (DID)
  
  - DID clásico
  
  - DID con múltiples períodos
  
  - DID con tratamiento escalonado

- Event studies

- Synthetic Control

- Regression Discontinuity Design (RDD)
  
  - Sharp RDD
  
  - Fuzzy RDD

- Matching
  
  - Propensity Score Matching
  
  - Nearest neighbor
  
  - Kernel matching

- Double Machine Learning (DML)

👉 **Core actual de políticas públicas**

---

# 📌 VIII. Modelos de Demanda y Oferta

### 12. Demanda

- Sistemas de demanda:
  
  - AIDS
  
  - QUAIDS
  
  - LES

- Elasticidades precio e ingreso

- Demanda discreta (logit / nested logit)

### 13. Oferta y costos

- Funciones de costo (Translog, Cobb-Douglas)

- Fronteras de producción

---

# 📌 IX. Modelos de Frontera y Eficiencia

### 14. Frontera Estocástica

- SFA (producción)

- SFA (costos)

- DEA (no paramétrico)

---

# 📌 X. Modelos de Duración y Supervivencia

### 15. Survival / Duration

- Exponential

- Weibull

- Cox proportional hazards

- Competing risks

- Discrete-time duration models

---

# 📌 XI. Modelos No Lineales y Semi-paramétricos

### 16. Modelos Avanzados

- Modelos no lineales (NLS)

- Modelos semiparamétricos

- Kernel regression

- Local polynomial regression

- Quantile regression

---

# 📌 XII. Modelos Estructurales (nivel alto)

### 17. Microeconometría estructural

- Modelos de utilidad aleatoria

- Estimación por simulación

- MSM (Method of Simulated Moments)

- MPEC

- Dynamic discrete choice (Rust models)

👉 Para **investigación de frontera**

---

# 📌 XIII. Diagnósticos y Tests (módulo transversal)

- Multicolinealidad (VIF)

- Heterocedasticidad (BP, White)

- Autocorrelación (DW, BG)

- Normalidad (JB)

- Specification tests (RESET)

- Influential points (Cook, leverage)

---

# 📌 XIV. Output académico (clave para adopción)

- Tablas tipo **Stata**

- Exportación:
  
  - LaTeX
  
  - Word
  
  - Excel

- Gráficos:
  
  - Marginal effects
  
  - Event studies
  
  - RD plots

---

## 🧠 Traducción directa a arquitectura de software

Tu sistema puede organizarse como:

- **Core numérico** (numpy, scipy)

- **Econometría** (statsmodels, linearmodels, custom code)

- **Causalidad** (econml-like, propio)

- **Frontend**:
  
  - Wizard por modelo
  
  - Parámetros visibles
  
  - Defaults razonables

- **Reproducibilidad**:
  
  - Log del modelo
  
  - Export del script generado

---

### 📌 Conclusión clara

Lo que estás planteando **no es un simple software**, es:

> 🔹 *Un framework completo de microeconometría aplicada, con interfaz gráfica, reproducible y académico.*

