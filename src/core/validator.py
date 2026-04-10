from __future__ import annotations

import pandas as pd

from .dataset import Dataset


def _obtener_frame(data, columns: list[str]) -> pd.DataFrame:
    if isinstance(data, Dataset):
        return data.select(columns).query().copy()

    if isinstance(data, pd.DataFrame):
        return data[columns].copy()

    raise TypeError("Se esperaba un Dataset o un pandas DataFrame.")


def validar_variable_binaria(data, y_col):
    errores = []
    frame = _obtener_frame(data, [y_col])
    valores = frame[y_col].dropna().unique().tolist()
    valores_ordenados = sorted(valores)
    valores_validos = {0, 1, False, True}
    valores_observados = set(valores)

    if len(valores_observados) != 2:
        errores.append(
            f"La variable dependiente '{y_col}' debe tener exactamente dos "
            f"categorías observadas para un modelo binario. Valores encontrados: "
            f"{valores_ordenados}"
        )
        return errores

    if not valores_observados.issubset(valores_validos):
        errores.append(
            f"La variable dependiente '{y_col}' debe estar codificada como 0 y 1 "
            f"para modelos binarios. Valores encontrados: {valores_ordenados}"
        )

    return errores


def validar_columnas(data, y_col, x_cols):
    errores = []
    if isinstance(data, Dataset):
        columnas = set(data.get_columns())
    elif isinstance(data, pd.DataFrame):
        columnas = set(data.columns)
    else:
        raise TypeError("Se esperaba un Dataset o un pandas DataFrame.")

    columnas_faltantes = [col for col in [y_col, *x_cols] if col not in columnas]
    if columnas_faltantes:
        errores.append(f"Faltan columnas en el dataset: {columnas_faltantes}")
    return errores


def validar_nulos(data, y_col, x_cols):
    errores = []
    cols = [y_col, *x_cols]
    frame = _obtener_frame(data, cols)
    nulos = frame[cols].isnull().sum()
    columnas_con_nulos = nulos[nulos > 0]

    if not columnas_con_nulos.empty:
        errores.append(
            "Hay valores faltantes en: "
            + ", ".join(f"{col}={cant}" for col, cant in columnas_con_nulos.items())
        )
    return errores


def validar_constantes(data, x_cols):
    advertencias = []
    frame = _obtener_frame(data, x_cols)
    for col in x_cols:
        if frame[col].nunique(dropna=True) <= 1:
            advertencias.append(f"La variable '{col}' es constante o casi constante")
    return advertencias


def validar_muestra(data, minimo=10):
    advertencias = []
    if isinstance(data, Dataset):
        size = data.get_shape()[0]
    else:
        size = len(data)

    if size < minimo:
        advertencias.append(
            f"Muy pocas observaciones: {size}. Se recomiendan al menos {minimo}"
        )
    return advertencias


def validar_correlacion(data, x_cols, umbral=0.9):
    advertencias = []
    if len(x_cols) < 2:
        return advertencias

    frame = _obtener_frame(data, x_cols)
    corr = frame[x_cols].corr(numeric_only=True)
    revisadas = set()
    for col1 in corr.columns:
        for col2 in corr.columns:
            if col1 == col2:
                continue

            par = tuple(sorted((col1, col2)))
            if par in revisadas:
                continue
            revisadas.add(par)

            valor = corr.loc[col1, col2]
            if abs(valor) >= umbral:
                advertencias.append(
                    f"Alta correlación entre '{col1}' y '{col2}': {valor:.4f}"
                )
    return advertencias


def ejecutar_validaciones(data, y_col, x_cols, method=None):
    errores = []
    advertencias = []

    errores.extend(validar_columnas(data, y_col, x_cols))
    if errores:
        return errores, advertencias

    errores.extend(validar_nulos(data, y_col, x_cols))
    if method in {"logit", "probit"}:
        errores.extend(validar_variable_binaria(data, y_col))

    advertencias.extend(validar_constantes(data, x_cols))
    advertencias.extend(validar_muestra(data))
    advertencias.extend(validar_correlacion(data, x_cols))
    return errores, advertencias
