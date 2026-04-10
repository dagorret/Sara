from __future__ import annotations

import math

import pandas as pd


def compare_states(a: dict, b: dict) -> dict:
    filters_a = list(a.get("filters", []))
    filters_b = list(b.get("filters", []))
    order_a = a.get("order_by")
    order_b = b.get("order_by")
    columns_a = list(a.get("selected_columns") or [])
    columns_b = list(b.get("selected_columns") or [])

    changed = []
    summary = []
    rows = []

    if filters_a != filters_b:
        changed.append({"field": "filters", "a": filters_a, "b": filters_b})
        rows.append(
            {
                "Categoria": "Query State",
                "Elemento": "Filtros",
                "Modelo A": _as_text(filters_a),
                "Modelo B": _as_text(filters_b),
                "Diferencia": _list_delta(filters_a, filters_b),
            }
        )
        summary.append("Cambios detectados en filtros activos.")

    if order_a != order_b:
        changed.append({"field": "order_by", "a": order_a, "b": order_b})
        rows.append(
            {
                "Categoria": "Query State",
                "Elemento": "Orden",
                "Modelo A": _as_text(order_a),
                "Modelo B": _as_text(order_b),
                "Diferencia": "Cambio en criterio de ordenamiento",
            }
        )
        summary.append("Cambió el orden aplicado al dataset.")

    if columns_a != columns_b:
        changed.append({"field": "selected_columns", "a": columns_a, "b": columns_b})
        rows.append(
            {
                "Categoria": "Query State",
                "Elemento": "Columnas visibles",
                "Modelo A": _as_text(columns_a),
                "Modelo B": _as_text(columns_b),
                "Diferencia": _list_delta(columns_a, columns_b),
            }
        )
        summary.append("Cambió la proyección de columnas visibles.")

    if a.get("dataset") != b.get("dataset"):
        changed.append({"field": "dataset", "a": a.get("dataset"), "b": b.get("dataset")})
        rows.append(
            {
                "Categoria": "Query State",
                "Elemento": "Dataset base",
                "Modelo A": _as_text(a.get("dataset")),
                "Modelo B": _as_text(b.get("dataset")),
                "Diferencia": "Cambio de dataset base",
            }
        )
        summary.append("Los estados comparados parten de datasets base distintos.")

    return {
        "changed": changed,
        "summary": summary,
        "table": pd.DataFrame(rows),
    }


def compare_dicts(a: dict, b: dict) -> dict:
    return compare_states(a, b)


def compare_datasets(
    *,
    shape_a: tuple[int, int],
    shape_b: tuple[int, int],
    columns_a: list[str],
    columns_b: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    rows = []
    summary = []

    row_delta = int(shape_b[0]) - int(shape_a[0])
    col_delta = int(shape_b[1]) - int(shape_a[1])
    rows.append(
        _comparison_row(
            "Dataset",
            "Filas",
            shape_a[0],
            shape_b[0],
            row_delta,
        )
    )
    rows.append(
        _comparison_row(
            "Dataset",
            "Columnas activas",
            shape_a[1],
            shape_b[1],
            col_delta,
        )
    )

    only_a = sorted(set(columns_a) - set(columns_b))
    only_b = sorted(set(columns_b) - set(columns_a))
    common = sorted(set(columns_a) & set(columns_b))

    rows.append(
        {
            "Categoria": "Dataset",
            "Elemento": "Solo en A",
            "Modelo A": _as_text(only_a),
            "Modelo B": "-",
            "Diferencia": f"{len(only_a)} columnas exclusivas",
        }
    )
    rows.append(
        {
            "Categoria": "Dataset",
            "Elemento": "Solo en B",
            "Modelo A": "-",
            "Modelo B": _as_text(only_b),
            "Diferencia": f"{len(only_b)} columnas exclusivas",
        }
    )
    rows.append(
        {
            "Categoria": "Dataset",
            "Elemento": "Columnas comunes",
            "Modelo A": len(common),
            "Modelo B": len(common),
            "Diferencia": "Base comparable",
        }
    )

    if row_delta != 0:
        direction = "más filas" if row_delta > 0 else "menos filas"
        summary.append(f"El estado B tiene {abs(row_delta):,} {direction} que A.")
    if col_delta != 0:
        direction = "más columnas activas" if col_delta > 0 else "menos columnas activas"
        summary.append(f"El estado B tiene {abs(col_delta):,} {direction} que A.")
    if only_a or only_b:
        summary.append("La estructura visible del dataset cambió entre ambos estados.")

    return pd.DataFrame(rows), summary


def compare_model_results(
    result_a,
    result_b,
    metrics_a: dict | None = None,
    metrics_b: dict | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    metrics_a = metrics_a or {}
    metrics_b = metrics_b or {}

    metric_specs = [
        (
            "R-cuadrado",
            _metric_value(result_a, metrics_a, "rsquared", "r2"),
            _metric_value(result_b, metrics_b, "rsquared", "r2"),
        ),
        (
            "R-cuadrado ajustado",
            _metric_value(result_a, metrics_a, "rsquared_adj", "adj_r2"),
            _metric_value(result_b, metrics_b, "rsquared_adj", "adj_r2"),
        ),
        (
            "Pseudo R-cuadrado",
            _metric_value(result_a, metrics_a, "prsquared"),
            _metric_value(result_b, metrics_b, "prsquared"),
        ),
        (
            "Accuracy",
            _metric_value(result_a, metrics_a, "accuracy"),
            _metric_value(result_b, metrics_b, "accuracy"),
        ),
        (
            "AUC",
            _metric_value(result_a, metrics_a, "auc"),
            _metric_value(result_b, metrics_b, "auc"),
        ),
        (
            "Precision",
            _metric_value(result_a, metrics_a, "precision"),
            _metric_value(result_b, metrics_b, "precision"),
        ),
        (
            "Recall",
            _metric_value(result_a, metrics_a, "recall"),
            _metric_value(result_b, metrics_b, "recall"),
        ),
        (
            "F1",
            _metric_value(result_a, metrics_a, "f1"),
            _metric_value(result_b, metrics_b, "f1"),
        ),
        (
            "Log-likelihood",
            _metric_value(result_a, metrics_a, "llf"),
            _metric_value(result_b, metrics_b, "llf"),
        ),
    ]

    rows = []
    summary = []
    for metric_name, a_value, b_value in metric_specs:
        if a_value is None and b_value is None:
            continue
        delta = _delta(a_value, b_value)
        rows.append(_comparison_row("Modelo", metric_name, a_value, b_value, delta))
        if delta is None or math.isclose(delta, 0.0, abs_tol=1e-12):
            continue
        direction = _metric_direction(metric_name, delta)
        summary.append(f"{metric_name}: Modelo {direction} ({delta:+.4f}).")

    params_a = getattr(result_a, "params", None)
    params_b = getattr(result_b, "params", None)
    pvalues_a = getattr(result_a, "pvalues", None)
    pvalues_b = getattr(result_b, "pvalues", None)
    if params_a is not None and params_b is not None:
        param_names = sorted(set(params_a.index) | set(params_b.index))
        for name in param_names:
            a_coef = params_a[name] if name in params_a.index else None
            b_coef = params_b[name] if name in params_b.index else None
            a_p = pvalues_a[name] if pvalues_a is not None and name in pvalues_a.index else None
            b_p = pvalues_b[name] if pvalues_b is not None and name in pvalues_b.index else None

            rows.append(
                _comparison_row(
                    "Coeficiente",
                    name,
                    a_coef,
                    b_coef,
                    _delta(a_coef, b_coef),
                )
            )
            rows.append(
                _comparison_row(
                    "P-Value",
                    name,
                    a_p,
                    b_p,
                    _delta(a_p, b_p),
                )
            )

            significance_summary = _compare_significance(name, a_p, b_p)
            if significance_summary:
                summary.append(significance_summary)

    return pd.DataFrame(rows), summary


def _metric_value(result, metrics: dict, attr_name: str, metric_key: str | None = None):
    key = metric_key or attr_name
    value = _safe_attr(result, attr_name)
    if value is not None:
        return value
    return _to_float(metrics.get(key))


def _safe_attr(obj, attr: str):
    try:
        value = getattr(obj, attr)
    except Exception:
        return None
    return _to_float(value)


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _fmt(value):
    if value is None:
        return "-"
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set, dict)):
        return _as_text(value)
    return f"{float(value):.4f}"


def _as_text(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, dict):
        parts = [f"{key}={value[key]}" for key in sorted(value.keys())]
        return ", ".join(parts) if parts else "-"
    if isinstance(value, (list, tuple, set)):
        items = [str(item) for item in value]
        return ", ".join(items) if items else "-"
    return str(value)


def _delta(a_value, b_value):
    a_number = _to_float(a_value)
    b_number = _to_float(b_value)
    if a_number is None or b_number is None:
        return None
    return b_number - a_number


def _comparison_row(category: str, element: str, a_value, b_value, delta):
    return {
        "Categoria": category,
        "Elemento": element,
        "Modelo A": _fmt(a_value),
        "Modelo B": _fmt(b_value),
        "Diferencia": _fmt(delta),
    }


def _list_delta(a_items: list, b_items: list) -> str:
    only_a = sorted(set(a_items) - set(b_items))
    only_b = sorted(set(b_items) - set(a_items))
    parts = []
    if only_a:
        parts.append(f"solo A: {', '.join(only_a)}")
    if only_b:
        parts.append(f"solo B: {', '.join(only_b)}")
    return " | ".join(parts) if parts else "Cambio de orden"


def _metric_direction(metric_name: str, delta: float) -> str:
    lower_is_better = {"Log-likelihood": False}
    if metric_name in lower_is_better:
        improved = delta > 0
    else:
        improved = delta > 0
    return f"B mejora respecto a A" if improved else f"B empeora respecto a A"


def _compare_significance(name: str, a_p, b_p) -> str | None:
    a_sig = _is_significant(a_p)
    b_sig = _is_significant(b_p)
    if a_sig is None or b_sig is None or a_sig == b_sig:
        return None
    if a_sig and not b_sig:
        return f"La variable {name} pierde significancia en el modelo B."
    return f"La variable {name} gana significancia en el modelo B."


def _is_significant(p_value) -> bool | None:
    number = _to_float(p_value)
    if number is None:
        return None
    return number < 0.05
