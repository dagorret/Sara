from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(slots=True)
class ModelResult:
    model_type: str
    coefficients: pd.Series
    pvalues: pd.Series
    metrics: dict[str, float | int | str | None]
    summary: str
    raw_result: object | None = None
    warnings: list[str] = field(default_factory=list)
    std_errors: pd.Series = field(default_factory=lambda: pd.Series(dtype="float64"))
    statistics: pd.Series = field(default_factory=lambda: pd.Series(dtype="float64"))
    confidence_intervals: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def from_statsmodels(
        cls,
        model_type: str,
        result,
        warnings: list[str] | None = None,
    ) -> "ModelResult":
        params = result.params
        pvalues = result.pvalues
        std_errors = getattr(result, "bse", pd.Series(dtype="float64"))
        statistics = getattr(result, "tvalues", pd.Series(dtype="float64"))
        conf_int = result.conf_int()

        try:
            summary_text = result.summary().as_text()
        except Exception:
            summary_text = str(result.summary())

        metrics = {
            "nobs": getattr(result, "nobs", None),
            "df_model": getattr(result, "df_model", None),
            "df_resid": getattr(result, "df_resid", None),
            "cov_type": getattr(result, "cov_type", None),
            "rsquared": getattr(result, "rsquared", None),
            "rsquared_adj": getattr(result, "rsquared_adj", None),
            "fvalue": getattr(result, "fvalue", None),
            "f_pvalue": getattr(result, "f_pvalue", None),
            "llf": getattr(result, "llf", None),
            "aic": getattr(result, "aic", None),
            "bic": getattr(result, "bic", None),
            "prsquared": getattr(result, "prsquared", None),
        }

        return cls(
            model_type=model_type,
            coefficients=params.astype("float64"),
            pvalues=pvalues.astype("float64"),
            metrics=metrics,
            summary=summary_text,
            raw_result=result,
            warnings=list(warnings or []),
            std_errors=std_errors.astype("float64"),
            statistics=statistics.astype("float64"),
            confidence_intervals=conf_int.copy(),
        )

    @property
    def params(self) -> pd.Series:
        return self.coefficients.copy()

    @property
    def bse(self) -> pd.Series:
        return self.std_errors.copy()

    @property
    def tvalues(self) -> pd.Series:
        return self.statistics.copy()

    def conf_int(self) -> pd.DataFrame:
        return self.confidence_intervals.copy()

    def predict(self, *args, **kwargs):
        if self.raw_result is None:
            raise AttributeError("El modelo no tiene un resultado subyacente para predecir.")
        return self.raw_result.predict(*args, **kwargs)

    def __getattr__(self, name: str):
        if self.raw_result is None:
            raise AttributeError(name)
        return getattr(self.raw_result, name)
