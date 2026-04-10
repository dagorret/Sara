from __future__ import annotations

import warnings

import pandas as pd
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import ConvergenceWarning, PerfectSeparationWarning

from .database import quote_identifier
from .dataset import Dataset


def _to_model_frame(data, columns: list[str]) -> pd.DataFrame:
    if isinstance(data, Dataset):
        return data.select(columns).query().dropna().copy()

    if isinstance(data, pd.DataFrame):
        return data[columns].dropna().copy()

    raise TypeError("Se esperaba un Dataset o un pandas DataFrame.")


def run_ols(data, y_col: str, x_cols: list[str]):
    frame = _to_model_frame(data, [y_col, *x_cols])
    y = frame[y_col]
    X = sm.add_constant(frame[x_cols], has_constant="add")
    modelo = sm.OLS(y, X)
    resultado = modelo.fit()
    return resultado, []


def run_logit(data, y_col: str, x_cols: list[str]):
    return _run_binary_model(sm.Logit, data, y_col, x_cols)


def run_probit(data, y_col: str, x_cols: list[str]):
    return _run_binary_model(sm.Probit, data, y_col, x_cols)


def _run_binary_model(model_class, data, y_col: str, x_cols: list[str]):
    frame = _to_model_frame(data, [y_col, *x_cols])
    y = frame[y_col].astype(int)
    X = sm.add_constant(frame[x_cols], has_constant="add")
    modelo = model_class(y, X)
    mensajes: list[str] = []
    mensajes_vistos: set[str] = set()

    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")
        resultado = modelo.fit(disp=False)

        for warning in captured_warnings:
            mensaje = None
            if issubclass(warning.category, PerfectSeparationWarning):
                mensaje = (
                    "Separación perfecta detectada: el modelo no es confiable "
                    "(predicción perfecta)."
                )
            elif issubclass(warning.category, ConvergenceWarning):
                mensaje = (
                    "El modelo no converge: los resultados pueden ser inestables."
                )

            if mensaje and mensaje not in mensajes_vistos:
                mensajes.append(mensaje)
                mensajes_vistos.add(mensaje)

    return resultado, mensajes


def correr_ols(data, y_col, x_cols):
    return run_ols(data, y_col, x_cols)


def correr_logit(data, y_col, x_cols):
    return run_logit(data, y_col, x_cols)


def correr_probit(data, y_col, x_cols):
    return run_probit(data, y_col, x_cols)
