from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

from .dataset import Dataset
from .regression import correr_logit, correr_probit


TOLERANCIA_EMPATE_TECNICO = 0.001


def _dividir_seguro(numerador, denominador):
    if denominador == 0:
        return 0.0
    return float(numerador / denominador)


def _tiene_advertencias_graves(mensajes_modelo):
    mensajes_modelo = mensajes_modelo or []
    return any(
        "Separación perfecta detectada" in mensaje
        or "no converge" in mensaje.lower()
        for mensaje in mensajes_modelo
    )


def _obtener_frame(data, columns: list[str]) -> pd.DataFrame:
    if isinstance(data, Dataset):
        return data.select(columns).query().copy()

    if isinstance(data, pd.DataFrame):
        return data[columns].copy()

    raise TypeError("Se esperaba un Dataset o un pandas DataFrame.")


def _preparar_datos_clasificacion(modelo, data, y_col, x_cols):
    frame = _obtener_frame(data, [y_col, *x_cols]).dropna().reset_index(drop=True)
    y_real = frame[y_col].astype(int)
    X = sm.add_constant(frame[x_cols], has_constant="add")
    probabilidades = pd.Series(modelo.predict(X), index=frame.index, name="probabilidad")
    return y_real, probabilidades


def _construir_matriz_confusion(y_real, y_pred):
    return pd.crosstab(
        y_real,
        y_pred,
        rownames=["Real"],
        colnames=["Predicho"],
        dropna=False,
    ).reindex(index=[0, 1], columns=[0, 1], fill_value=0)


def _calcular_metricas_clasificacion(matriz_confusion):
    verdaderos_negativos = int(matriz_confusion.loc[0, 0])
    falsos_positivos = int(matriz_confusion.loc[0, 1])
    falsos_negativos = int(matriz_confusion.loc[1, 0])
    verdaderos_positivos = int(matriz_confusion.loc[1, 1])

    total = (
        verdaderos_negativos
        + falsos_positivos
        + falsos_negativos
        + verdaderos_positivos
    )

    accuracy = _dividir_seguro(verdaderos_positivos + verdaderos_negativos, total)
    precision = _dividir_seguro(
        verdaderos_positivos,
        verdaderos_positivos + falsos_positivos,
    )
    recall = _dividir_seguro(
        verdaderos_positivos,
        verdaderos_positivos + falsos_negativos,
    )
    f1 = _dividir_seguro(2 * precision * recall, precision + recall)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "resumen_confusion": {
            "verdaderos_negativos": verdaderos_negativos,
            "falsos_positivos": falsos_positivos,
            "falsos_negativos": falsos_negativos,
            "verdaderos_positivos": verdaderos_positivos,
        },
    }


def calcular_r2(y_real, y_pred):
    y_real = pd.Series(y_real)
    y_pred = pd.Series(y_pred)
    residual = ((y_real - y_pred) ** 2).sum()
    total = ((y_real - y_real.mean()) ** 2).sum()
    return 1.0 - _dividir_seguro(residual, total)


def evaluar_regresion(modelo):
    predicciones = pd.Series(modelo.fittedvalues, name="prediccion")
    reales = pd.Series(modelo.model.endog, name="real")
    return {
        "r2": calcular_r2(reales, predicciones),
        "predicciones": pd.DataFrame({"real": reales, "prediccion": predicciones}),
    }


def construir_curva_roc(y_real, probabilidades):
    datos = (
        pd.DataFrame({"y_real": y_real.astype(int), "probabilidad": probabilidades})
        .sort_values("probabilidad", ascending=False)
        .reset_index(drop=True)
    )

    positivos = int((datos["y_real"] == 1).sum())
    negativos = int((datos["y_real"] == 0).sum())
    filas = [{"threshold": float("inf"), "tpr": 0.0, "fpr": 0.0}]

    if positivos == 0 or negativos == 0:
        filas.append({"threshold": float("-inf"), "tpr": 1.0, "fpr": 1.0})
        return pd.DataFrame(filas)

    tp = 0
    fp = 0
    for threshold, grupo in datos.groupby("probabilidad", sort=False):
        tp += int((grupo["y_real"] == 1).sum())
        fp += int((grupo["y_real"] == 0).sum())
        filas.append(
            {
                "threshold": float(threshold),
                "tpr": _dividir_seguro(tp, positivos),
                "fpr": _dividir_seguro(fp, negativos),
            }
        )

    if filas[-1]["tpr"] != 1.0 or filas[-1]["fpr"] != 1.0:
        filas.append({"threshold": float("-inf"), "tpr": 1.0, "fpr": 1.0})

    return pd.DataFrame(filas)


def calcular_auc(roc_curve):
    auc = 0.0
    for i in range(1, len(roc_curve)):
        x_anterior = float(roc_curve.iloc[i - 1]["fpr"])
        x_actual = float(roc_curve.iloc[i]["fpr"])
        y_anterior = float(roc_curve.iloc[i - 1]["tpr"])
        y_actual = float(roc_curve.iloc[i]["tpr"])
        auc += (x_actual - x_anterior) * (y_actual + y_anterior) / 2
    return float(auc)


def evaluar_clasificacion(modelo, data, y_col, x_cols, threshold=0.5):
    y_real, probabilidades = _preparar_datos_clasificacion(modelo, data, y_col, x_cols)
    y_pred = (probabilidades >= threshold).astype(int)
    matriz_confusion = _construir_matriz_confusion(y_real, y_pred)
    metricas = _calcular_metricas_clasificacion(matriz_confusion)
    curva_roc = construir_curva_roc(y_real, probabilidades)
    auc = calcular_auc(curva_roc)

    predicciones = pd.DataFrame(
        {
            "real": y_real,
            "probabilidad_predicha": probabilidades,
            "clase_predicha": y_pred,
            "threshold_usado": threshold,
        }
    )

    return {
        "threshold": threshold,
        "accuracy": metricas["accuracy"],
        "precision": metricas["precision"],
        "recall": metricas["recall"],
        "f1": metricas["f1"],
        "auc": auc,
        "matriz_confusion": matriz_confusion,
        "resumen_confusion": metricas["resumen_confusion"],
        "roc_curve": curva_roc,
        "predicciones": predicciones,
    }


def evaluar_thresholds(modelo, data, y_col, x_cols, thresholds=None):
    if thresholds is None:
        thresholds = [i / 10 for i in range(1, 10)]

    y_real, probabilidades = _preparar_datos_clasificacion(modelo, data, y_col, x_cols)
    filas = []

    for threshold in thresholds:
        y_pred = (probabilidades >= threshold).astype(int)
        matriz_confusion = _construir_matriz_confusion(y_real, y_pred)
        metricas = _calcular_metricas_clasificacion(matriz_confusion)
        filas.append(
            {
                "threshold": float(threshold),
                "accuracy": metricas["accuracy"],
                "precision": metricas["precision"],
                "recall": metricas["recall"],
                "f1": metricas["f1"],
            }
        )

    tabla = pd.DataFrame(filas)
    mejor = tabla.sort_values(["f1", "threshold"], ascending=[False, True]).iloc[0]
    return {
        "tabla": tabla,
        "mejor_threshold": float(mejor["threshold"]),
        "f1_maximo": float(mejor["f1"]),
        "rango_evaluado": (
            float(tabla["threshold"].min()),
            float(tabla["threshold"].max()),
        ),
    }


def detectar_sesgo(matriz_confusion):
    falsos_positivos = int(matriz_confusion.loc[0, 1])
    falsos_negativos = int(matriz_confusion.loc[1, 0])

    if falsos_positivos == falsos_negativos:
        return {
            "sesgo": "equilibrado",
            "mensaje": "Sin sesgo claro entre falsos positivos y falsos negativos.",
        }
    if falsos_positivos > falsos_negativos:
        return {
            "sesgo": "clase_positiva",
            "mensaje": (
                "El modelo tiende a predecir clase positiva "
                "(muchos falsos positivos)."
            ),
        }
    return {
        "sesgo": "clase_negativa",
        "mensaje": (
            "El modelo tiende a predecir clase negativa "
            "(muchos falsos negativos)."
        ),
    }


def calcular_balance(data, y_col):
    frame = _obtener_frame(data, [y_col]).dropna()
    conteos = frame[y_col].astype(int).value_counts().reindex([0, 1], fill_value=0)
    total = int(conteos.sum())
    porcentaje_clase_0 = _dividir_seguro(int(conteos.loc[0]), total)
    porcentaje_clase_1 = _dividir_seguro(int(conteos.loc[1]), total)
    return {
        "clase_0": porcentaje_clase_0,
        "clase_1": porcentaje_clase_1,
        "desbalanceado": min(porcentaje_clase_0, porcentaje_clase_1) < 0.2,
    }


def score_modelo(evaluacion, mensajes_modelo=None):
    mensajes_modelo = mensajes_modelo or []
    score = (0.6 * evaluacion["auc"]) + (0.4 * evaluacion["f1"])
    sesgo = detectar_sesgo(evaluacion["matriz_confusion"])
    if sesgo["sesgo"] != "equilibrado":
        score -= 0.05
    if any("Separación perfecta detectada" in mensaje for mensaje in mensajes_modelo):
        score -= 0.3
    if any("no converge" in mensaje.lower() for mensaje in mensajes_modelo):
        score -= 0.1
    return max(0.0, min(1.0, float(score)))


def comparar_modelos(data, y_col, x_cols, threshold=0.5):
    modelos = [("Logit", correr_logit), ("Probit", correr_probit)]
    filas = []
    detalles = {}

    for nombre, runner in modelos:
        modelo, mensajes_modelo = runner(data, y_col, x_cols)
        evaluacion = evaluar_clasificacion(
            modelo,
            data,
            y_col,
            x_cols,
            threshold=threshold,
        )
        score = score_modelo(evaluacion, mensajes_modelo)
        filas.append(
            {
                "Modelo": nombre,
                "AUC": evaluacion["auc"],
                "F1": evaluacion["f1"],
                "Accuracy": evaluacion["accuracy"],
                "Score": score,
            }
        )
        detalles[nombre.lower()] = {
            "modelo": modelo,
            "mensajes_modelo": mensajes_modelo,
            "evaluacion": evaluacion,
            "score": score,
            "advertencias_graves": _tiene_advertencias_graves(mensajes_modelo),
        }

    tabla = pd.DataFrame(filas)
    tabla_ordenada = tabla.sort_values(
        ["AUC", "F1", "Accuracy"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    mejor = tabla_ordenada.iloc[0]
    segundo = tabla_ordenada.iloc[1] if len(tabla_ordenada) > 1 else None
    empate_tecnico = False
    motivo = "mayor AUC"

    if segundo is not None:
        diferencia_auc = abs(float(mejor["AUC"]) - float(segundo["AUC"]))
        diferencia_f1 = abs(float(mejor["F1"]) - float(segundo["F1"]))
        if (
            diferencia_auc < TOLERANCIA_EMPATE_TECNICO
            and diferencia_f1 < TOLERANCIA_EMPATE_TECNICO
        ):
            empate_tecnico = True
            motivo = (
                "No hay diferencia sustancial entre Logit y Probit. "
                "Ambos modelos muestran desempeño muy similar."
            )
        elif float(mejor["AUC"]) > float(segundo["AUC"]) and float(mejor["F1"]) >= float(segundo["F1"]):
            motivo = "mayor AUC y mejor balance precision/recall"
        elif float(mejor["AUC"]) == float(segundo["AUC"]) and float(mejor["F1"]) > float(segundo["F1"]):
            motivo = "AUC empatada y mejor F1"

    return {
        "tabla": tabla_ordenada,
        "mejor_modelo": str(mejor["Modelo"]),
        "motivo": motivo,
        "score": float(mejor["Score"]),
        "detalles": detalles,
        "empate_tecnico": empate_tecnico,
    }


def generar_diagnostico(evaluacion, balance=None, mensajes_modelo=None):
    if not evaluacion:
        return []

    mensajes_modelo = mensajes_modelo or []
    mensajes = []
    advertencias_graves = _tiene_advertencias_graves(mensajes_modelo)

    if any("Separación perfecta detectada" in mensaje for mensaje in mensajes_modelo):
        mensajes.append("Modelo inválido (separación perfecta detectada).")
    elif any("no converge" in mensaje.lower() for mensaje in mensajes_modelo):
        mensajes.append("Modelo inestable (problemas de convergencia).")

    sesgo = detectar_sesgo(evaluacion["matriz_confusion"])
    if sesgo["sesgo"] == "clase_positiva":
        mensajes.append("Ligera tendencia a falsos positivos.")
    elif sesgo["sesgo"] == "clase_negativa":
        mensajes.append("Ligera tendencia a falsos negativos.")

    if balance and balance["desbalanceado"]:
        mensajes.append("Dataset desbalanceado.")

    if advertencias_graves:
        if (
            evaluacion["auc"] >= 0.99
            or evaluacion["f1"] >= 0.99
            or evaluacion["accuracy"] >= 0.99
        ):
            mensajes.append(
                "Métricas perfectas pueden deberse a un dataset patológico, "
                "no a un buen modelo."
            )
    else:
        if evaluacion["auc"] > 0.9:
            mensajes.append("Buen poder predictivo (AUC > 0.9).")
        elif evaluacion["auc"] >= 0.8:
            mensajes.append("Poder predictivo aceptable.")

    if (
        evaluacion["accuracy"] >= 0.8
        and evaluacion["f1"] >= 0.8
        and sesgo["sesgo"] == "equilibrado"
        and not advertencias_graves
    ):
        mensajes.insert(0, "Modelo estable.")

    if not mensajes:
        mensajes.append("Modelo con comportamiento razonable.")

    return mensajes


def analizar_clasificacion(modelo, data, y_col, x_cols, threshold=0.5, mensajes_modelo=None):
    evaluacion = evaluar_clasificacion(modelo, data, y_col, x_cols, threshold=threshold)
    analisis_thresholds = evaluar_thresholds(modelo, data, y_col, x_cols)
    sesgo = detectar_sesgo(evaluacion["matriz_confusion"])
    balance = calcular_balance(data, y_col)
    score = score_modelo(evaluacion, mensajes_modelo)
    diagnostico = generar_diagnostico(
        evaluacion,
        balance=balance,
        mensajes_modelo=mensajes_modelo,
    )
    comparacion = comparar_modelos(data, y_col, x_cols, threshold=threshold)

    evaluacion["analisis_automatico"] = {
        "thresholds_evaluados": analisis_thresholds["tabla"]["threshold"].tolist(),
        "mejor_threshold": analisis_thresholds["mejor_threshold"],
        "f1_maximo": analisis_thresholds["f1_maximo"],
        "rango_evaluado": analisis_thresholds["rango_evaluado"],
        "tabla_thresholds": analisis_thresholds["tabla"],
        "sesgo": sesgo,
        "diagnostico": diagnostico,
    }
    evaluacion["balance_clases"] = balance
    evaluacion["comparacion_modelos"] = comparacion
    evaluacion["score"] = score
    evaluacion["diagnostico_avanzado"] = diagnostico
    evaluacion["advertencias_graves"] = _tiene_advertencias_graves(mensajes_modelo)
    return evaluacion
