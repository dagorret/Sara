from __future__ import annotations

import logging

import pandas as pd
from pandas.api.types import is_numeric_dtype

from .config import SIGNIFICANCE_LEVEL
from .dataset import Dataset
from .exceptions import ValidationError


log = logging.getLogger(__name__)


def _obtener_frame(data, columns: list[str]) -> pd.DataFrame:
    if isinstance(data, Dataset):
        return data.select(columns).query().copy()

    if isinstance(data, pd.DataFrame):
        missing = [column for column in columns if column not in data.columns]
        if missing:
            raise ValidationError(f"Faltan columnas en el dataset: {missing}")
        return data[columns].copy()

    raise ValidationError("Se esperaba un Dataset o un pandas DataFrame.")


def _dataset_columns(data) -> list[str]:
    if isinstance(data, Dataset):
        return data.get_base_columns()
    if isinstance(data, pd.DataFrame):
        return list(data.columns)
    raise ValidationError("Se esperaba un Dataset o un pandas DataFrame.")


def validate_columns_exist(dataset, columns):
    requested = [str(column) for column in columns]
    available = set(_dataset_columns(dataset))
    missing = [column for column in requested if column not in available]
    if missing:
        raise ValidationError(f"Columnas no encontradas en el dataset: {missing}")


def validate_numeric_columns(dataset, columns):
    validate_columns_exist(dataset, columns)
    requested = [str(column) for column in columns]

    if isinstance(dataset, Dataset):
        metadata = dataset.get_metadata()
        non_numeric = [
            column
            for column in requested
            if not Dataset._is_numeric_type(str(metadata["types"][column]))
        ]
    else:
        non_numeric = [column for column in requested if not is_numeric_dtype(dataset[column])]

    if non_numeric:
        raise ValidationError(
            f"Las columnas deben ser numéricas para modelar: {non_numeric}"
        )


def validate_no_nulls(dataset, columns):
    validate_columns_exist(dataset, columns)
    requested = [str(column) for column in columns]

    if isinstance(dataset, Dataset):
        metadata = dataset.get_metadata()
        invalid = {
            column: int(metadata["null_counts"][column])
            for column in requested
            if int(metadata["null_counts"][column]) > 0
        }
    else:
        null_counts = dataset[requested].isnull().sum()
        invalid = {
            column: int(count)
            for column, count in null_counts.items()
            if int(count) > 0
        }

    if invalid:
        detail = ", ".join(f"{column}={count}" for column, count in invalid.items())
        raise ValidationError(f"Hay valores nulos en columnas requeridas: {detail}")


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
    try:
        validate_columns_exist(data, [y_col, *x_cols])
    except ValidationError as exc:
        return [str(exc)]
    return []


def validar_nulos(data, y_col, x_cols):
    try:
        validate_no_nulls(data, [y_col, *x_cols])
    except ValidationError as exc:
        return [str(exc)]
    return []


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

    log.info("Running validations for method=%s, y=%s, X=%s", method, y_col, x_cols)

    errores.extend(validar_columnas(data, y_col, x_cols))
    if errores:
        return errores, advertencias

    try:
        validate_numeric_columns(data, [y_col, *x_cols])
    except ValidationError as exc:
        errores.append(str(exc))

    errores.extend(validar_nulos(data, y_col, x_cols))
    if method in {"logit", "probit"}:
        errores.extend(validar_variable_binaria(data, y_col))

    advertencias.extend(validar_constantes(data, x_cols))
    advertencias.extend(validar_muestra(data))
    advertencias.extend(validar_correlacion(data, x_cols))
    return errores, advertencias


def es_significativo(pvalue: float | None, alpha: float = SIGNIFICANCE_LEVEL) -> bool:
    if pvalue is None:
        return False
    return float(pvalue) < float(alpha)
