from __future__ import annotations

import logging
import warnings

import pandas as pd
import statsmodels.api as sm
from statsmodels.tools.sm_exceptions import ConvergenceWarning, PerfectSeparationWarning

from .config import DEFAULT_THRESHOLD
from .dataset import Dataset
from .exceptions import ModelError, ValidationError
from .model_result import ModelResult
from .validator import (
    validate_columns_exist,
    validate_no_nulls,
    validate_numeric_columns,
    validar_variable_binaria,
)


log = logging.getLogger(__name__)


def _to_model_frame(data, columns: list[str]) -> pd.DataFrame:
    if isinstance(data, Dataset):
        return data.select(columns).query().copy()

    if isinstance(data, pd.DataFrame):
        missing = [column for column in columns if column not in data.columns]
        if missing:
            raise ValidationError(f"Faltan columnas en el dataset: {missing}")
        return data[columns].copy()

    raise ValidationError("Se esperaba un Dataset o un pandas DataFrame.")


def _validate_model_input(data, y_col: str, x_cols: list[str], method: str) -> None:
    columns = [y_col, *x_cols]
    validate_columns_exist(data, columns)
    validate_numeric_columns(data, columns)
    validate_no_nulls(data, columns)

    if method in {"logit", "probit"}:
        errores_binarios = validar_variable_binaria(data, y_col)
        if errores_binarios:
            raise ValidationError(errores_binarios[0])


def _fit_model(model_type: str, model_factory, data, y_col: str, x_cols: list[str]):
    _validate_model_input(data, y_col, x_cols, model_type)
    frame = _to_model_frame(data, [y_col, *x_cols])
    y = frame[y_col].astype(int) if model_type in {"logit", "probit"} else frame[y_col]
    X = sm.add_constant(frame[x_cols], has_constant="add")
    modelo = model_factory(y, X)

    mensajes: list[str] = []
    mensajes_vistos: set[str] = set()

    try:
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            resultado = modelo.fit(disp=False) if model_type in {"logit", "probit"} else modelo.fit()

        for warning in captured_warnings:
            mensaje = None
            if issubclass(warning.category, PerfectSeparationWarning):
                mensaje = (
                    "Separación perfecta detectada: el modelo no es confiable "
                    "(predicción perfecta)."
                )
            elif issubclass(warning.category, ConvergenceWarning):
                mensaje = "El modelo no converge: los resultados pueden ser inestables."

            if mensaje and mensaje not in mensajes_vistos:
                mensajes.append(mensaje)
                mensajes_vistos.add(mensaje)
    except ValidationError:
        raise
    except Exception as exc:
        log.error("Model fitting failed for %s with y=%s and X=%s: %s", model_type, y_col, x_cols, exc)
        raise ModelError(
            f"No se pudo ajustar el modelo {model_type.upper()} con y='{y_col}' y X={x_cols}."
        ) from exc

    log.info("Model %s fitted successfully with %s observations", model_type, len(frame))
    return ModelResult.from_statsmodels(model_type, resultado, warnings=mensajes), mensajes


def run_ols(data, y_col: str, x_cols: list[str]):
    log.info("Running OLS with y=%s and X=%s", y_col, x_cols)
    return _fit_model("ols", sm.OLS, data, y_col, x_cols)


def run_logit(data, y_col: str, x_cols: list[str]):
    log.info("Running Logit with y=%s and X=%s", y_col, x_cols)
    return _fit_model("logit", sm.Logit, data, y_col, x_cols)


def run_probit(data, y_col: str, x_cols: list[str]):
    log.info("Running Probit with y=%s and X=%s", y_col, x_cols)
    return _fit_model("probit", sm.Probit, data, y_col, x_cols)


def run_pipeline(dataset, y, X, model_type, threshold: float = DEFAULT_THRESHOLD):
    from .evaluation import analizar_clasificacion, evaluar_regresion
    from .report import generate_technical_report

    normalized_model = str(model_type).strip().lower()
    runners = {
        "ols": run_ols,
        "logit": run_logit,
        "probit": run_probit,
    }
    if normalized_model not in runners:
        raise ModelError(f"Método no soportado: {model_type}")

    result, warnings_list = runners[normalized_model](dataset, y, X)
    if normalized_model == "ols":
        evaluation = evaluar_regresion(result)
    else:
        evaluation = analizar_clasificacion(
            result,
            dataset,
            y,
            X,
            threshold=threshold,
            mensajes_modelo=warnings_list,
        )

    report = generate_technical_report(result, metrics=evaluation, method=normalized_model)
    return {
        "result": result,
        "evaluation": evaluation,
        "report": report,
        "warnings": warnings_list,
    }


def correr_ols(data, y_col, x_cols):
    return run_ols(data, y_col, x_cols)


def correr_logit(data, y_col, x_cols):
    return run_logit(data, y_col, x_cols)


def correr_probit(data, y_col, x_cols):
    return run_probit(data, y_col, x_cols)
