# 📊 Plataforma Académica de Estadística y Econometría

## Documento base — Módulo Estadística + Puente a Econometría (Plan 3.5)

---

## 🟢 MÓDULO 0 — ESTADÍSTICA (BASE TRANSVERSAL)

Este módulo está pensado para:

- Docencia universitaria
- Investigación básica
- Carreras no econométricas
- Usuarios sin formación econométrica

Es la **base común** de toda la plataforma.

---

## 1️⃣ Estadística Descriptiva

### Medidas resumen

- Media
- Mediana
- Moda (opcional)
- Varianza
- Desvío estándar
- Mínimo / Máximo
- Percentiles

### Tablas

- Tablas de frecuencia
- Tablas cruzadas
- Tablas por grupos

### Gráficos

- Histogramas
- Boxplots
- Gráficos de barras
- Series simples (si hay tiempo)

Objetivo:

> Describir datos sin inferir ni explicar causalidad.

---

## 2️⃣ Estadística Inferencial

Introduce la idea de **inferir sobre una población a partir de una muestra**.

### Intervalos de confianza

- Para la media
- Para proporciones
- Nivel configurable (95% por defecto)

### Tests clásicos

#### Test t

- Una muestra
- Dos muestras independientes
- Muestras pareadas

Usos típicos:

- Comparación de grupos
- Antes vs después

#### Test Chi-cuadrado (χ²)

- Independencia
- Bondad de ajuste

Muy usado en:

- Encuestas
- Variables categóricas

---

## 3️⃣ ANOVA

- ANOVA de una vía
- Comparación de medias entre múltiples grupos

Mensaje pedagógico clave:

> ANOVA generaliza el test t a más de dos grupos.

---

## 4️⃣ Regresión Lineal Simple

Puente natural entre estadística e inferencia explicativa.

Modelo:
\[
y = \alpha + \beta x
\]

### Contenidos

- Interpretación de la pendiente
- Intercepto
- R²
- Test t sobre coeficientes
- Intervalos de confianza

Aclaración importante:

> Todavía NO es econometría causal.

---

# 🟡 PLAN 3.5 — REGRESIONES MÚLTIPLES, ENDOGENEIDAD Y CAUSALIDAD

*(Contenido presente en los programas, pero poco usado en la práctica)*

Este plan actúa como **puente conceptual** hacia la econometría aplicada.

---

## 3.5.1 Regresión Lineal Múltiple

Modelo:
\[
y = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \varepsilon
\]

### Conceptos clave

- Interpretación **condicional** (ceteris paribus)
- Controlar por variables observables

### Problemas habituales

- Multicolinealidad
- Mala interpretación de coeficientes
- Confusión entre correlación y causalidad

### Aporte del sistema

- Selección guiada de variables
- Advertencias automáticas:
  - alta correlación entre regresores
  - pocos grados de libertad
- Tabla clara estilo Stata
- Interpretación textual básica

---

## 3.5.2 Endogeneidad (conceptual)

Definición simple:

> Una variable explicativa está correlacionada con el error.

Ejemplos didácticos:

- Educación ↔ ingresos (habilidad no observada)
- Precio ↔ cantidad (simultaneidad)

### Qué se enseña

- Por qué OLS puede estar sesgado
- Cuándo sospechar endogeneidad

### UX pedagógica

Mensajes del sistema como:

> “Este modelo asume exogeneidad. Evalúe si es razonable.”

---

## 3.5.3 Correlación vs Causalidad

Mensajes clave:

- Regresión ≠ causalidad
- Correlación ≠ efecto causal

### Herramientas didácticas

- Gráficos comparativos
- Simulaciones simples
- Comparación entre:
  - regresión simple
  - regresión con controles

Objetivo:

> Ordenar conceptos que suelen confundirse.

---

## 3.5.4 Introducción a Instrumentos (sin formalismo)

### Idea central

Una variable instrumental:

- Está correlacionada con X
- No está correlacionada con el error

Ejemplos típicos:

- Distancia
- Reglas administrativas
- Variables naturales

### Qué NO se hace aún

- 2SLS formal
- Tests de instrumentos

Este punto **prepara** al usuario para econometría aplicada (V1).

---

## 3.5.5 UX del Plan 3.5

Modo **Académico Guiado**:

- Selección de outcome
- Múltiples regresores
- Mensajes conceptuales automáticos

Ejemplo:

> “Los resultados muestran asociaciones condicionadas, no efectos causales.”

---

## 3.5.6 Valor del Plan 3.5

### Académico

- Permite enseñar lo que hoy se omite
- Respeta programas oficiales

### Institucional

- Reduce la brecha teoría–práctica
- Empodera a docentes no econometristas

### Estratégico

- Prepara a usuarios para:
  - econometría aplicada
  - DID
  - IV
  - evaluación de políticas

---

## 4️⃣ Relación con el Roadmap General

- Módulo Estadística → base común
- Plan 3.5 → transición conceptual
- V1 → econometría aplicada formal

---

## 🧠 Conclusión

Este módulo no requiere ser econometrista.
Permite:

- enseñar mejor
- usar datos reales
- reducir barreras técnicas
- construir confianza en el sistema

Es el **punto de entrada natural** para la Facultad.
