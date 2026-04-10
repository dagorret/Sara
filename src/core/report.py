from __future__ import annotations

from pathlib import Path

import pandas as pd
from statsmodels.stats.stattools import durbin_watson


METODOS = {
    "ols": "Mínimos Cuadrados Ordinarios (OLS)",
    "logit": "Modelo Logit",
    "probit": "Modelo Probit",
}


def _formatear_float(valor, decimales=4):
    if valor is None:
        return "N/A"

    try:
        if pd.isna(valor):
            return "N/A"
    except TypeError:
        pass

    try:
        return f"{float(valor):.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)


def formatear_valor(valor, decimales=4):
    if isinstance(valor, bool):
        return str(valor)

    if isinstance(valor, int):
        return str(valor)

    return _formatear_float(valor, decimales)


def imprimir_reporte_validacion(errores, advertencias):
    print("\n=== VALIDACIONES ===")

    if not errores and not advertencias:
        print("OK: no se encontraron problemas")
        return

    if errores:
        print("\nErrores:")
        for error in errores:
            print(f" - {error}")

    if advertencias:
        print("\nAdvertencias:")
        for advertencia in advertencias:
            print(f" - {advertencia}")


def imprimir_advertencias_modelo(mensajes_modelo):
    if not mensajes_modelo:
        return

    print("\n=== ADVERTENCIAS DEL MODELO ===")
    for mensaje in mensajes_modelo:
        print(f" - {mensaje}")


def construir_tabla_coeficientes(modelo):
    conf_int = modelo.conf_int()

    filas = []
    for nombre in modelo.params.index:
        filas.append(
            {
                "Variable": nombre,
                "Coeficiente": modelo.params[nombre],
                "Error estándar": modelo.bse[nombre],
                "Estadístico": modelo.tvalues[nombre],
                "Valor p": modelo.pvalues[nombre],
                "IC 2.5%": conf_int.loc[nombre, 0],
                "IC 97.5%": conf_int.loc[nombre, 1],
            }
        )

    return pd.DataFrame(filas)


def formatear_tabla_coeficientes(tabla):
    tabla_mostrar = tabla.copy()
    columnas_numericas = [
        "Coeficiente",
        "Error estándar",
        "Estadístico",
        "Valor p",
        "IC 2.5%",
        "IC 97.5%",
    ]

    for col in columnas_numericas:
        tabla_mostrar[col] = tabla_mostrar[col].apply(_formatear_float)

    return tabla_mostrar


def obtener_informacion_general(modelo, metodo):
    nombre_metodo = METODOS.get(metodo, metodo.upper())

    return [
        ("Método", nombre_metodo),
        ("Variable dependiente", modelo.model.endog_names),
        ("Observaciones", int(modelo.nobs)),
        ("Grados de libertad (modelo)", int(modelo.df_model)),
        ("Grados de libertad (residuos)", int(modelo.df_resid)),
        ("Tipo de covarianza", modelo.cov_type),
    ]


def obtener_medidas_ajuste(modelo, metodo):
    medidas = []

    if metodo == "ols":
        medidas.extend(
            [
                ("R-cuadrado", modelo.rsquared),
                ("R-cuadrado ajustado", modelo.rsquared_adj),
                ("Estadístico F", modelo.fvalue),
                ("Probabilidad(F)", modelo.f_pvalue),
            ]
        )

    if hasattr(modelo, "llf"):
        medidas.append(("Log-verosimilitud", modelo.llf))

    if hasattr(modelo, "aic"):
        medidas.append(("AIC", modelo.aic))

    if hasattr(modelo, "bic"):
        medidas.append(("BIC", modelo.bic))

    if metodo in {"logit", "probit"}:
        try:
            medidas.append(("Pseudo R-cuadrado", modelo.prsquared))
        except Exception:
            medidas.append(("Pseudo R-cuadrado", "N/A"))

    return medidas


def obtener_diagnostico_basico(modelo, metodo):
    diagnostico = []

    if metodo == "ols":
        try:
            diagnostico.append(("Durbin-Watson", durbin_watson(modelo.resid)))
        except Exception:
            diagnostico.append(("Durbin-Watson", "N/A"))

        try:
            diagnostico.append(("Número de condición", modelo.condition_number))
        except Exception:
            diagnostico.append(("Número de condición", "N/A"))

    elif metodo in {"logit", "probit"}:
        nombre = "Logit" if metodo == "logit" else "Probit"
        diagnostico.append(("Durbin-Watson", f"no aplica a {nombre}"))
        diagnostico.append(("Número de condición", "no disponible"))

    return diagnostico


def obtener_interpretacion_rapida(tabla, metodo, modelo_con_problemas):
    interpretaciones = []

    if modelo_con_problemas:
        interpretaciones.append("El modelo presenta advertencias importantes.")
        interpretaciones.append(
            "La interpretación de coeficientes y valores p puede no ser confiable."
        )
        return interpretaciones

    for _, fila in tabla.iterrows():
        variable = fila["Variable"]

        if variable == "const":
            continue

        coef = fila["Coeficiente"]
        pvalor = fila["Valor p"]

        significancia = "significativo" if pvalor < 0.05 else "no significativo"

        if metodo == "ols":
            if coef > 0:
                direccion = "aumenta"
            elif coef < 0:
                direccion = "disminuye"
            else:
                direccion = "no modifica"

            interpretaciones.append(
                f"{variable}: coeficiente = {_formatear_float(coef)}, "
                f"efecto {significancia} (p = {_formatear_float(pvalor)}), "
                f"por lo que un aumento en esta variable {direccion} "
                f"la variable dependiente."
            )

        elif metodo in {"logit", "probit"}:
            if coef > 0:
                direccion = "aumenta"
            elif coef < 0:
                direccion = "disminuye"
            else:
                direccion = "no modifica"

            nombre = "Logit" if metodo == "logit" else "Probit"
            escala = (
                "el logaritmo de las odds del evento"
                if metodo == "logit"
                else "el índice latente asociado a la probabilidad del evento"
            )

            interpretaciones.append(
                f"{variable}: coeficiente = {_formatear_float(coef)}, "
                f"efecto {significancia} (p = {_formatear_float(pvalor)}). "
                f"En un modelo {nombre}, un aumento en esta variable {direccion} "
                f"{escala}."
            )

    return interpretaciones


def obtener_bloque_evaluacion_clasificacion(evaluacion):
    if not evaluacion:
        return []

    return [
        ("Threshold usado", evaluacion["threshold"]),
        ("Accuracy", evaluacion["accuracy"]),
        ("Precision", evaluacion["precision"]),
        ("Recall", evaluacion["recall"]),
        ("F1", evaluacion["f1"]),
        ("AUC", evaluacion["auc"]),
    ]


def obtener_bloque_analisis_automatico(evaluacion):
    if not evaluacion:
        return []

    analisis = evaluacion.get("analisis_automatico")
    if not analisis:
        return []

    rango_inicial, rango_final = analisis["rango_evaluado"]

    return [
        (
            "Thresholds evaluados",
            f"{formatear_valor(rango_inicial, 1)} - {formatear_valor(rango_final, 1)}",
        ),
        ("Mejor threshold sugerido", analisis["mejor_threshold"]),
        ("F1 máximo", analisis["f1_maximo"]),
    ]


def obtener_lineas_diagnostico_automatico(evaluacion):
    if not evaluacion:
        return []

    analisis = evaluacion.get("analisis_automatico")
    if not analisis:
        return []

    lineas = []
    for mensaje in analisis["diagnostico"]:
        if mensaje in {
            "Modelo estable.",
            "Buen poder predictivo (AUC > 0.9).",
            "Poder predictivo aceptable.",
        }:
            prefijo = "✔"
        else:
            prefijo = "⚠"
        lineas.append(f"{prefijo} {mensaje}")

    return lineas


def formatear_tabla_comparacion_modelos(comparacion):
    tabla = comparacion["tabla"].copy()
    for col in ["AUC", "F1", "Accuracy", "Score"]:
        tabla[col] = tabla[col].apply(formatear_valor)
    return tabla.to_string(index=False)


def obtener_lineas_comparacion_modelos(evaluacion):
    if not evaluacion:
        return []

    comparacion = evaluacion.get("comparacion_modelos")
    if not comparacion:
        return []

    lineas = [formatear_tabla_comparacion_modelos(comparacion), ""]

    if comparacion.get("empate_tecnico"):
        lineas.append("No hay diferencia sustancial entre Logit y Probit.")
        lineas.append("Ambos modelos muestran desempeño muy similar.")
    else:
        lineas.append(
            f"Mejor modelo: {comparacion['mejor_modelo']} (según AUC)"
        )

    return lineas


def obtener_bloque_balance_clases(evaluacion):
    if not evaluacion:
        return []

    balance = evaluacion.get("balance_clases")
    if not balance:
        return []

    return [
        ("Clase 0", f"{formatear_valor(balance['clase_0'] * 100, 2)}%"),
        ("Clase 1", f"{formatear_valor(balance['clase_1'] * 100, 2)}%"),
    ]


def obtener_lineas_diagnostico_avanzado(evaluacion):
    if not evaluacion:
        return []

    diagnostico = evaluacion.get("diagnostico_avanzado")
    if not diagnostico:
        return []

    lineas = []
    for mensaje in diagnostico:
        if "inválido" in mensaje.lower():
            prefijo = "✘"
        elif mensaje in {
            "Modelo estable.",
            "Buen poder predictivo (AUC > 0.9).",
            "Poder predictivo aceptable.",
        }:
            prefijo = "✔"
        else:
            prefijo = "⚠"
        lineas.append(f"{prefijo} {mensaje}")

    return lineas


def obtener_lineas_recomendacion_final(evaluacion):
    if not evaluacion:
        return []

    comparacion = evaluacion.get("comparacion_modelos")
    if not comparacion:
        return []

    if comparacion.get("empate_tecnico"):
        return [
            "No hay una recomendación fuerte entre Logit y Probit.",
            f"Motivo: {comparacion['motivo']}",
            f"Score de referencia: {formatear_valor(comparacion['score'])}",
        ]

    return [
        f"Modelo recomendado: {comparacion['mejor_modelo']}",
        f"Motivo: {comparacion['motivo']}",
        f"Score: {formatear_valor(comparacion['score'])}",
    ]


def formatear_matriz_confusion(matriz_confusion):
    return matriz_confusion.to_string()


def _imprimir_bloque_items(titulo, items):
    print(f"\n{titulo}:")
    for etiqueta, valor in items:
        print(f" - {etiqueta}: {formatear_valor(valor)}")


def _imprimir_interpretacion(interpretaciones):
    print("\nInterpretación rápida:")
    for interpretacion in interpretaciones:
        print(f" - {interpretacion}")


def _imprimir_coeficientes(modelo):
    print("\nCoeficientes:")
    tabla = construir_tabla_coeficientes(modelo)
    tabla_mostrar = formatear_tabla_coeficientes(tabla)
    print(tabla_mostrar.to_string(index=False))


def imprimir_evaluacion_clasificacion(evaluacion):
    if not evaluacion:
        return

    print("\n=== EVALUACIÓN DEL MODELO ===")

    for etiqueta, valor in obtener_bloque_evaluacion_clasificacion(evaluacion):
        print(f"{etiqueta}: {formatear_valor(valor)}")

    print("\nMatriz de confusión:")
    print(formatear_matriz_confusion(evaluacion["matriz_confusion"]))


def imprimir_analisis_automatico(evaluacion):
    if not evaluacion:
        return

    print("\n=== ANÁLISIS AUTOMÁTICO ===")
    for etiqueta, valor in obtener_bloque_analisis_automatico(evaluacion):
        print(f"{etiqueta}: {valor if isinstance(valor, str) else formatear_valor(valor)}")


def imprimir_diagnostico_automatico(evaluacion):
    if not evaluacion:
        return

    print("\n=== DIAGNÓSTICO AUTOMÁTICO ===")
    for linea in obtener_lineas_diagnostico_automatico(evaluacion):
        print(linea)


def imprimir_comparacion_modelos(evaluacion):
    if not evaluacion:
        return

    print("\n=== COMPARACIÓN DE MODELOS ===")
    for i, linea in enumerate(obtener_lineas_comparacion_modelos(evaluacion)):
        if i == 0:
            print(linea)
        elif linea:
            print(f"\n{linea}")


def imprimir_balance_clases(evaluacion):
    if not evaluacion:
        return

    print("\n=== BALANCE DE CLASES ===")
    for etiqueta, valor in obtener_bloque_balance_clases(evaluacion):
        print(f"{etiqueta}: {valor}")

    balance = evaluacion.get("balance_clases")
    if balance and balance["desbalanceado"]:
        print("\n⚠ Dataset desbalanceado (posible sesgo en métricas)")


def imprimir_diagnostico_avanzado(evaluacion):
    if not evaluacion:
        return

    print("\n=== DIAGNÓSTICO AVANZADO ===")
    for linea in obtener_lineas_diagnostico_avanzado(evaluacion):
        print(linea)


def imprimir_recomendacion_final(evaluacion):
    if not evaluacion:
        return

    print("\n=== RECOMENDACIÓN FINAL ===")
    for linea in obtener_lineas_recomendacion_final(evaluacion):
        print(linea)


def imprimir_resumen_modelo(modelo, metodo, mensajes_modelo=None):
    if mensajes_modelo is None:
        mensajes_modelo = []

    modelo_con_problemas = len(mensajes_modelo) > 0
    tabla = construir_tabla_coeficientes(modelo)
    informacion_general = obtener_informacion_general(modelo, metodo)
    medidas_ajuste = obtener_medidas_ajuste(modelo, metodo)
    diagnostico = obtener_diagnostico_basico(modelo, metodo)
    interpretaciones = obtener_interpretacion_rapida(
        tabla,
        metodo,
        modelo_con_problemas,
    )

    print("\n=== RESULTADOS DEL MODELO ===\n")

    _imprimir_bloque_items("Información general", informacion_general)
    _imprimir_bloque_items("Medidas de ajuste", medidas_ajuste)
    _imprimir_coeficientes(modelo)
    _imprimir_bloque_items("Diagnóstico básico", diagnostico)
    _imprimir_interpretacion(interpretaciones)


def inferir_metodo(modelo) -> str:
    model_name = modelo.model.__class__.__name__.lower()
    if "logit" in model_name:
        return "logit"
    if "probit" in model_name:
        return "probit"
    return "ols"


def _asegurar_path(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _extraer_variables_explicativas(modelo) -> list[str]:
    names = list(modelo.params.index)
    return [name for name in names if name != "const"]


def _evaluar_calidad_modelo(metodo: str, metrics: dict | None) -> str:
    metrics = metrics or {}
    if metodo == "ols":
        r2 = metrics.get("r2", getattr(metrics, "rsquared", None))
        if r2 is None:
            return "No hay suficientes métricas para evaluar el ajuste."
        if r2 > 0.6:
            return "El modelo muestra un buen ajuste global."
        return "El modelo muestra un ajuste limitado y conviene revisar especificación."

    auc = metrics.get("auc")
    if auc is None:
        return "No hay suficiente información para evaluar el poder predictivo."
    if auc > 0.8:
        return "El modelo presenta buen poder predictivo."
    if auc >= 0.7:
        return "El modelo presenta poder predictivo aceptable."
    return "El modelo presenta capacidad predictiva limitada."


def _generar_lineas_interpretacion(tabla: pd.DataFrame, metodo: str) -> list[str]:
    lineas = []
    for _, fila in tabla.iterrows():
        variable = fila["Variable"]
        if variable == "const":
            continue

        coef = float(fila["Coeficiente"])
        pvalor = float(fila["Valor p"])
        efecto = "positivo" if coef > 0 else "negativo" if coef < 0 else "nulo"
        significativo = pvalor < 0.05

        if metodo == "ols":
            if significativo:
                lineas.append(
                    f"La variable {variable} tiene un efecto {efecto} y "
                    f"estadisticamente significativo sobre la variable dependiente. "
                    f"Un aumento de una unidad en {variable} cambia Y en "
                    f"{_formatear_float(coef)} unidades en promedio."
                )
            else:
                lineas.append(
                    f"No se encuentra evidencia estadistica de que {variable} "
                    f"tenga un efecto distinto de cero sobre la variable dependiente "
                    f"(p = {_formatear_float(pvalor)})."
                )
        else:
            nombre = "Logit" if metodo == "logit" else "Probit"
            escala = (
                "las log-odds del evento"
                if metodo == "logit"
                else "el indice latente de la probabilidad del evento"
            )
            if significativo:
                lineas.append(
                    f"La variable {variable} tiene un efecto {efecto} y "
                    f"estadisticamente significativo en el modelo {nombre}. "
                    f"Un aumento en {variable} modifica {escala} en "
                    f"{_formatear_float(coef)}."
                )
            else:
                lineas.append(
                    f"No se encuentra evidencia estadistica de efecto para {variable} "
                    f"en el modelo {nombre} (p = {_formatear_float(pvalor)})."
                )
    return lineas


def _render_items(items: list[tuple[str, object]]) -> str:
    return "\n".join(f" - {etiqueta}: {formatear_valor(valor)}" for etiqueta, valor in items)


def generate_simple_report(result, metrics: dict | None = None, method: str | None = None) -> str:
    metodo = method or inferir_metodo(result)
    variables = _extraer_variables_explicativas(result)
    tabla = construir_tabla_coeficientes(result)
    lineas = [
        f"Modelo {METODOS.get(metodo, metodo.upper())}.",
        f"Variables explicativas: {', '.join(variables) if variables else 'ninguna'}.",
        "Se estimaron coeficientes y niveles de significancia.",
        "",
        "Coeficientes resumidos:",
    ]
    for _, fila in tabla.iterrows():
        lineas.append(
            f" - {fila['Variable']}: coef={_formatear_float(fila['Coeficiente'])}, "
            f"p={_formatear_float(fila['Valor p'])}"
        )
    if metrics:
        lineas.append("")
        lineas.append(_evaluar_calidad_modelo(metodo, metrics))
    return "\n".join(lineas)


def generate_technical_report(result, metrics: dict | None = None, method: str | None = None) -> str:
    metodo = method or inferir_metodo(result)
    tabla = construir_tabla_coeficientes(result)
    metrics = metrics or {}

    lineas = [
        "=== MODELO ===",
        _render_items(obtener_informacion_general(result, metodo)),
        "",
        "=== COEFICIENTES ===",
        formatear_tabla_coeficientes(tabla).to_string(index=False),
        "",
        "=== METRICAS ===",
        _render_items(obtener_medidas_ajuste(result, metodo)),
    ]

    metricas_extra = []
    if metodo == "ols" and "r2" in metrics:
        metricas_extra.append(("R2 evaluado", metrics["r2"]))
    if metodo in {"logit", "probit"}:
        for key in ("accuracy", "auc", "precision", "recall", "f1", "threshold"):
            if key in metrics:
                metricas_extra.append((key.upper(), metrics[key]))
    if metricas_extra:
        lineas.extend(["", _render_items(metricas_extra)])

    lineas.extend(
        [
            "",
            "=== DIAGNOSTICO ===",
            _render_items(obtener_diagnostico_basico(result, metodo)),
        ]
    )
    return "\n".join(lineas)


def generate_interpretative_report(result, metrics: dict | None = None, method: str | None = None) -> str:
    metodo = method or inferir_metodo(result)
    tabla = construir_tabla_coeficientes(result)
    variables = _extraer_variables_explicativas(result)
    calidad = _evaluar_calidad_modelo(metodo, metrics or {})
    lineas = [
        f"Se estimó un modelo {METODOS.get(metodo, metodo.upper())} con las variables "
        f"{', '.join(variables) if variables else 'seleccionadas por el usuario'}.",
        calidad,
        "",
        "Interpretacion economica:",
    ]
    lineas.extend(f" - {linea}" for linea in _generar_lineas_interpretacion(tabla, metodo))
    return "\n".join(lineas)


def generate_paper_report(
    result,
    metrics: dict | None = None,
    method: str | None = None,
    output_format: str = "txt",
) -> str:
    metodo = method or inferir_metodo(result)
    metrics = metrics or {}
    tabla = construir_tabla_coeficientes(result)
    dependent = result.model.endog_names
    variables = _extraer_variables_explicativas(result)

    secciones = [
        (
            "Introducción",
            [
                _build_paper_intro(metodo, dependent, variables),
            ],
        ),
        (
            "Metodología",
            [
                _build_paper_methodology(metodo, int(result.nobs)),
            ],
        ),
        (
            "Resultados",
            _build_paper_results(tabla, metodo, dependent),
        ),
        (
            "Calidad del Modelo",
            _build_paper_quality(result, metrics, metodo),
        ),
        (
            "Discusión",
            _build_paper_discussion(tabla, metrics, metodo),
        ),
        (
            "Conclusión",
            [
                _build_paper_conclusion(tabla, metrics, metodo, dependent),
            ],
        ),
    ]

    normalized_format = output_format.strip().lower()
    if normalized_format == "markdown":
        return _render_paper_markdown(secciones)
    if normalized_format == "latex":
        return _render_paper_latex(secciones)
    return _render_paper_txt(secciones)


def generate_comparative_report(
    result_a,
    result_b,
    metrics_a: dict | None = None,
    metrics_b: dict | None = None,
    label_a: str = "Modelo A",
    label_b: str = "Modelo B",
) -> str:
    metodo_a = inferir_metodo(result_a)
    metodo_b = inferir_metodo(result_b)
    metrics_a = metrics_a or {}
    metrics_b = metrics_b or {}

    lineas = [
        f"Comparacion entre {label_a} ({METODOS.get(metodo_a, metodo_a)}) y "
        f"{label_b} ({METODOS.get(metodo_b, metodo_b)}).",
    ]

    comparisons = []
    for metric_name, key in (
        ("AUC", "auc"),
        ("Accuracy", "accuracy"),
        ("R2", "r2"),
        ("Log-likelihood", "log_likelihood"),
    ):
        a_value = metrics_a.get(key, getattr(result_a, "llf", None) if key == "log_likelihood" else None)
        b_value = metrics_b.get(key, getattr(result_b, "llf", None) if key == "log_likelihood" else None)
        if a_value is None or b_value is None:
            continue
        delta = float(b_value) - float(a_value)
        winner = label_b if delta > 0 else label_a if delta < 0 else "ambos"
        comparisons.append(
            f"{metric_name}: {label_b} - {label_a} = {_formatear_float(delta)}. "
            f"Mejor desempeno: {winner}."
        )

    if comparisons:
        lineas.extend(comparisons)
    else:
        lineas.append("No hay suficientes metricas comparables para establecer una diferencia concluyente.")

    return "\n".join(lineas)


def generate_report(result, metrics: dict | None = None, report_type: str = "interpretative") -> str:
    normalized = report_type.strip().lower()
    if normalized == "simple":
        return generate_simple_report(result, metrics=metrics)
    if normalized == "technical":
        return generate_technical_report(result, metrics=metrics)
    if normalized == "interpretative":
        return generate_interpretative_report(result, metrics=metrics)
    if normalized == "paper":
        return generate_paper_report(result, metrics=metrics)
    raise ValueError(f"Tipo de reporte no soportado: {report_type}")


def export_txt(report: str, path: str | Path) -> Path:
    output_path = _asegurar_path(path)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def export_csv(coefficients: pd.DataFrame, path: str | Path) -> Path:
    output_path = _asegurar_path(path)
    coefficients.to_csv(output_path, index=False)
    return output_path


def export_predictions(predictions: pd.DataFrame, path: str | Path) -> Path:
    output_path = _asegurar_path(path)
    predictions.to_csv(output_path, index=False)
    return output_path


def export_markdown(report: str, path: str | Path) -> Path:
    output_path = _asegurar_path(path)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def export_latex(report: str, path: str | Path) -> Path:
    output_path = _asegurar_path(path)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def _build_paper_intro(metodo: str, dependent: str, variables: list[str]) -> str:
    variables_text = ", ".join(variables) if variables else "un conjunto de covariables seleccionadas"
    return (
        f"Se estima un modelo para analizar los determinantes de {dependent} "
        f"utilizando como variables explicativas {variables_text}. "
        f"El objetivo es identificar qué factores muestran asociación estadística "
        f"con la variable dependiente y en qué dirección opera dicho efecto."
    )


def _build_paper_methodology(metodo: str, nobs: int) -> str:
    metodo_texto = METODOS.get(metodo, metodo.upper())
    if metodo == "ols":
        detalle = (
            "La estimación se realiza mediante mínimos cuadrados ordinarios, "
            "lo que permite cuantificar cambios promedio en la variable dependiente "
            "ante variaciones marginales en las covariables."
        )
    else:
        detalle = (
            f"La especificación utiliza un modelo {metodo_texto}, adecuado para "
            "variables dependientes binarias y para modelar la probabilidad del evento "
            "de interés a partir de un índice lineal en las covariables."
        )
    return f"{detalle} La muestra efectiva utilizada en la estimación contiene {nobs:,} observaciones."


def _build_paper_results(tabla: pd.DataFrame, metodo: str, dependent: str) -> list[str]:
    lineas = []
    for _, fila in tabla.iterrows():
        variable = fila["Variable"]
        if variable == "const":
            continue
        coef = float(fila["Coeficiente"])
        pvalor = float(fila["Valor p"])
        se = float(fila["Error estándar"])
        efecto = "positivo" if coef > 0 else "negativo" if coef < 0 else "nulo"
        if pvalor < 0.05:
            if metodo == "ols":
                lineas.append(
                    f"La variable {variable} presenta un coeficiente {efecto} y estadísticamente "
                    f"significativo (coef. = {_formatear_float(coef)}, error estándar = {_formatear_float(se)}, "
                    f"p = {_formatear_float(pvalor)}), lo que sugiere que un incremento en {variable} "
                    f"se asocia con cambios promedio en {dependent} de {_formatear_float(coef)} unidades."
                )
            else:
                lineas.append(
                    f"La variable {variable} exhibe un efecto {efecto} y estadísticamente significativo "
                    f"(coef. = {_formatear_float(coef)}, error estándar = {_formatear_float(se)}, "
                    f"p = {_formatear_float(pvalor)}), indicando que incrementos en {variable} modifican "
                    f"la propensión estimada del evento bajo el modelo {METODOS.get(metodo, metodo.upper())}."
                )
        else:
            lineas.append(
                f"No se encuentra evidencia estadística suficiente para afirmar que {variable} "
                f"afecte a {dependent} al nivel convencional del 5% "
                f"(coef. = {_formatear_float(coef)}, p = {_formatear_float(pvalor)})."
            )
    return lineas or ["No se identificaron covariables distintas del intercepto para interpretar."]


def _build_paper_quality(result, metrics: dict, metodo: str) -> list[str]:
    lineas = []
    if metodo == "ols":
        r2 = metrics.get("r2", getattr(result, "rsquared", None))
        if r2 is not None:
            calidad = _evaluar_calidad_modelo(metodo, metrics)
            lineas.append(
                f"{calidad} "
                f"El coeficiente de determinación alcanza un valor de {_formatear_float(r2)}."
            )
        if hasattr(result, "condition_number"):
            lineas.append(
                f"El número de condición es {_formatear_float(result.condition_number)}, "
                "lo que sirve como referencia preliminar para evaluar posibles problemas de colinealidad."
            )
        try:
            dw = durbin_watson(result.resid)
            lineas.append(
                f"El estadístico Durbin-Watson toma un valor de {_formatear_float(dw)}, "
                "útil para una inspección básica de autocorrelación en los residuos."
            )
        except Exception:
            pass
        return lineas

    auc = metrics.get("auc")
    accuracy = metrics.get("accuracy")
    llf = getattr(result, "llf", None)
    if auc is not None:
        lineas.append(
            f"El poder predictivo del modelo se resume en un AUC de {_formatear_float(auc)}, "
            f"por lo que {_evaluar_calidad_modelo(metodo, metrics).lower()}"
        )
    if accuracy is not None:
        lineas.append(
            f"La tasa de clasificación correcta alcanza {_formatear_float(accuracy)}, "
            "lo que complementa la evaluación del desempeño predictivo."
        )
    if llf is not None:
        lineas.append(
            f"La log-verosimilitud del modelo es {_formatear_float(llf)}, "
            "magnitud útil para comparaciones entre especificaciones anidadas o alternativas."
        )
    return lineas or ["No hay métricas suficientes para evaluar la calidad del modelo."]


def _build_paper_discussion(tabla: pd.DataFrame, metrics: dict, metodo: str) -> list[str]:
    significativas = []
    no_significativas = []
    for _, fila in tabla.iterrows():
        variable = fila["Variable"]
        if variable == "const":
            continue
        if float(fila["Valor p"]) < 0.05:
            significativas.append(variable)
        else:
            no_significativas.append(variable)

    lineas = []
    if significativas:
        lineas.append(
            "Las variables con mayor respaldo empírico en la especificación son "
            f"{', '.join(significativas)}, dado que mantienen significancia estadística."
        )
    if no_significativas:
        lineas.append(
            "Algunas covariables no muestran evidencia concluyente, en particular "
            f"{', '.join(no_significativas)}, lo que sugiere cautela en la interpretación causal."
        )
    lineas.append(
        "Como en toda especificación aplicada, los resultados deben interpretarse considerando "
        "potenciales variables omitidas, problemas de medición y la naturaleza observacional de los datos."
    )
    if metodo in {"logit", "probit"} and "auc" in metrics and float(metrics["auc"]) < 0.7:
        lineas.append(
            "La capacidad predictiva es moderada o limitada, por lo que podrían explorarse "
            "especificaciones alternativas o variables adicionales."
        )
    if metodo == "ols" and "r2" in metrics and float(metrics["r2"]) < 0.6:
        lineas.append(
            "El ajuste global sugiere que parte de la variabilidad de la variable dependiente "
            "permanece sin explicar."
        )
    return lineas


def _build_paper_conclusion(tabla: pd.DataFrame, metrics: dict, metodo: str, dependent: str) -> str:
    significativas = [
        fila["Variable"]
        for _, fila in tabla.iterrows()
        if fila["Variable"] != "const" and float(fila["Valor p"]) < 0.05
    ]
    if significativas:
        variables_text = ", ".join(significativas)
        cierre = (
            f"En síntesis, la evidencia sugiere que {variables_text} constituyen determinantes "
            f"estadísticamente relevantes de {dependent} en la especificación analizada."
        )
    else:
        cierre = (
            f"En síntesis, la especificación analizada no identifica covariables con evidencia "
            f"estadística robusta para explicar {dependent}."
        )

    recomendacion = (
        "Se recomienda complementar este análisis con especificaciones alternativas, "
        "pruebas de robustez y, cuando corresponda, un diseño empírico que fortalezca "
        "la interpretación sustantiva de los resultados."
    )
    return f"{cierre} {recomendacion}"


def _render_paper_txt(secciones: list[tuple[str, list[str]]]) -> str:
    bloques = []
    for titulo, parrafos in secciones:
        bloques.append(titulo.upper())
        bloques.extend(parrafos)
        bloques.append("")
    return "\n".join(bloques).strip()


def _render_paper_markdown(secciones: list[tuple[str, list[str]]]) -> str:
    bloques = []
    for titulo, parrafos in secciones:
        bloques.append(f"## {titulo}")
        bloques.extend(parrafos)
        bloques.append("")
    return "\n".join(bloques).strip()


def _render_paper_latex(secciones: list[tuple[str, list[str]]]) -> str:
    bloques = []
    for titulo, parrafos in secciones:
        bloques.append(f"\\section{{{_latex_escape(titulo)}}}")
        bloques.extend(_latex_escape(parrafo) for parrafo in parrafos)
        bloques.append("")
    return "\n\n".join(bloques).strip()


def _latex_escape(texto: str) -> str:
    escaped = texto
    for source, target in (
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
    ):
        escaped = escaped.replace(source, target)
    return escaped
