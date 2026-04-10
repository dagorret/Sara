from pathlib import Path

from .report import (
    construir_tabla_coeficientes,
    formatear_matriz_confusion,
    formatear_tabla_coeficientes,
    formatear_valor,
    obtener_bloque_analisis_automatico,
    obtener_bloque_balance_clases,
    obtener_bloque_evaluacion_clasificacion,
    obtener_diagnostico_basico,
    obtener_informacion_general,
    obtener_interpretacion_rapida,
    obtener_lineas_comparacion_modelos,
    obtener_lineas_diagnostico_automatico,
    obtener_lineas_diagnostico_avanzado,
    obtener_lineas_recomendacion_final,
    obtener_medidas_ajuste,
)


def _asegurar_directorio(path_salida):
    path = Path(path_salida)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _agregar_bloque_items(lineas, titulo, items):
    if not items:
        return

    lineas.append(f"{titulo}:")
    for etiqueta, valor in items:
        lineas.append(f" - {etiqueta}: {formatear_valor(valor)}")
    lineas.append("")


def _agregar_bloque_lineas(lineas, titulo, items):
    if not items:
        return

    lineas.append(f"{titulo}:")
    lineas.extend(items)
    lineas.append("")


def _agregar_bloque_validaciones(lineas, errores, advertencias):
    lineas.append("Validaciones:")

    if not errores and not advertencias:
        lineas.append(" - OK: no se encontraron problemas")
        lineas.append("")
        return

    if errores:
        lineas.append("Errores:")
        for error in errores:
            lineas.append(f" - {error}")

    if advertencias:
        lineas.append("Advertencias:")
        for advertencia in advertencias:
            lineas.append(f" - {advertencia}")

    lineas.append("")


def _modelo_invalido(mensajes_modelo):
    for mensaje in mensajes_modelo:
        if "Separación perfecta detectada" in mensaje:
            return "⚠ Modelo inválido: separación perfecta detectada"

    return None


def exportar_reporte_txt(
    path_salida,
    modelo,
    metodo,
    errores=None,
    advertencias=None,
    mensajes_modelo=None,
    evaluacion=None,
):
    errores = errores or []
    advertencias = advertencias or []
    mensajes_modelo = mensajes_modelo or []

    tabla = construir_tabla_coeficientes(modelo)
    interpretaciones = obtener_interpretacion_rapida(
        tabla,
        metodo,
        len(mensajes_modelo) > 0,
    )

    lineas = ["=== RESULTADOS DEL MODELO ===", ""]

    _agregar_bloque_validaciones(lineas, errores, advertencias)

    mensaje_invalidez = _modelo_invalido(mensajes_modelo)
    if mensaje_invalidez:
        lineas.append(mensaje_invalidez)
        lineas.append("")

    if mensajes_modelo:
        lineas.append("Advertencias del modelo:")
        for mensaje in mensajes_modelo:
            lineas.append(f" - {mensaje}")
        lineas.append("")

    _agregar_bloque_items(
        lineas,
        "Información general",
        obtener_informacion_general(modelo, metodo),
    )
    _agregar_bloque_items(
        lineas,
        "Medidas de ajuste",
        obtener_medidas_ajuste(modelo, metodo),
    )

    lineas.append("Coeficientes:")
    lineas.append(formatear_tabla_coeficientes(tabla).to_string(index=False))
    lineas.append("")

    _agregar_bloque_items(
        lineas,
        "Diagnóstico básico",
        obtener_diagnostico_basico(modelo, metodo),
    )

    if evaluacion:
        _agregar_bloque_items(
            lineas,
            "Evaluación del modelo",
            obtener_bloque_evaluacion_clasificacion(evaluacion),
        )
        lineas.append("Matriz de confusión:")
        lineas.append(formatear_matriz_confusion(evaluacion["matriz_confusion"]))
        lineas.append("")
        _agregar_bloque_items(
            lineas,
            "Análisis automático",
            obtener_bloque_analisis_automatico(evaluacion),
        )
        _agregar_bloque_lineas(
            lineas,
            "Diagnóstico automático",
            obtener_lineas_diagnostico_automatico(evaluacion),
        )
        _agregar_bloque_lineas(
            lineas,
            "Comparación de modelos",
            obtener_lineas_comparacion_modelos(evaluacion),
        )
        _agregar_bloque_items(
            lineas,
            "Balance de clases",
            obtener_bloque_balance_clases(evaluacion),
        )

        balance = evaluacion.get("balance_clases")
        if balance and balance["desbalanceado"]:
            lineas.append("⚠ Dataset desbalanceado (posible sesgo en métricas)")
            lineas.append("")

        _agregar_bloque_lineas(
            lineas,
            "Diagnóstico avanzado",
            obtener_lineas_diagnostico_avanzado(evaluacion),
        )
        _agregar_bloque_lineas(
            lineas,
            "Recomendación final",
            obtener_lineas_recomendacion_final(evaluacion),
        )

    lineas.append("Interpretación rápida:")
    for interpretacion in interpretaciones:
        lineas.append(f" - {interpretacion}")
    lineas.append("")

    path = _asegurar_directorio(path_salida)
    path.write_text("\n".join(lineas), encoding="utf-8")

def exportar_coeficientes_csv(path_salida, modelo, evaluacion=None):
    tabla = construir_tabla_coeficientes(modelo).copy()

    if evaluacion:
        tabla["Threshold usado"] = evaluacion["threshold"]
        tabla["Accuracy"] = evaluacion["accuracy"]
        tabla["Precision"] = evaluacion["precision"]
        tabla["Recall"] = evaluacion["recall"]
        tabla["F1"] = evaluacion["f1"]
        tabla["AUC"] = evaluacion["auc"]
        tabla["Probabilidad media predicha"] = evaluacion["predicciones"][
            "probabilidad_predicha"
        ].mean()

    path = _asegurar_directorio(path_salida)
    tabla.to_csv(path, index=False)


def exportar_predicciones_csv(path_salida, evaluacion):
    if not evaluacion:
        return False

    path = _asegurar_directorio(path_salida)
    evaluacion["predicciones"].to_csv(path, index=False)
    return True
