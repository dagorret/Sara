from __future__ import annotations

from pathlib import Path

import pandas as pd

from desktop_app.models.dataset_model import DatasetModel
from src.core.compare import compare_datasets, compare_model_results, compare_states
from src.core.database import DuckDBManager
from src.core.dataset import Dataset
from src.core.evaluation import evaluar_clasificacion, evaluar_regresion
from src.core.loader import list_datasets, load_dataset, load_existing_dataset
from src.core.regression import run_logit, run_ols, run_probit
from src.core.report import (
    construir_tabla_coeficientes,
    generate_interpretative_report,
    generate_paper_report,
    generate_simple_report,
    generate_technical_report,
)


class DatasetService:
    def load_dataset(self, path: str) -> DatasetModel:
        dataset = load_dataset(path)
        return DatasetModel(dataset=dataset)

    def list_datasets(self) -> list[str]:
        return list_datasets()

    def get_dataset(self, table_name: str) -> DatasetModel:
        return DatasetModel(dataset=load_existing_dataset(table_name))

    def run_ols(self, dataset: DatasetModel, y_column: str, x_columns: list[str]):
        return run_ols(dataset.dataset, y_column, x_columns)

    def run_logit(self, dataset: DatasetModel, y_column: str, x_columns: list[str]):
        return run_logit(dataset.dataset, y_column, x_columns)

    def run_probit(self, dataset: DatasetModel, y_column: str, x_columns: list[str]):
        return run_probit(dataset.dataset, y_column, x_columns)

    def get_metadata(self, dataset: DatasetModel) -> dict[str, object]:
        return dataset.get_metadata()

    def build_model_metrics(self, result, dataset: DatasetModel, state: dict) -> dict:
        model_type = (state.get("model_type") or "").lower()
        y = state.get("y")
        x = state.get("x", [])
        if not y or not x:
            return {}
        if model_type in {"logit", "probit"}:
            return evaluar_clasificacion(result, dataset.dataset, y, x)
        if model_type == "ols":
            return evaluar_regresion(result)
        return {}

    def build_coefficients(self, result) -> pd.DataFrame:
        return construir_tabla_coeficientes(result)[
            ["Variable", "Coeficiente", "Valor p"]
        ].rename(columns={"Coeficiente": "Coeficiente", "Valor p": "p-value"})

    def build_report_bundle(self, result, metrics: dict, method: str) -> dict[str, str]:
        normalized_method = str(method).lower()
        return {
            "simple": generate_simple_report(result, metrics=metrics, method=normalized_method),
            "technical": generate_technical_report(result, metrics=metrics, method=normalized_method),
            "interpretative": generate_interpretative_report(
                result,
                metrics=metrics,
                method=normalized_method,
            ),
            "markdown": generate_paper_report(
                result,
                metrics=metrics,
                method=normalized_method,
                output_format="markdown",
            ),
            "latex": generate_paper_report(
                result,
                metrics=metrics,
                method=normalized_method,
                output_format="latex",
            ),
        }

    def export_report_text(self, report_text: str, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text, encoding="utf-8")
        return output_path

    def export_coefficients_csv(self, coefficients: pd.DataFrame, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        coefficients.to_csv(output_path, index=False)
        return output_path

    def save_analysis(
        self,
        *,
        name: str,
        dataset: DatasetModel,
        model_type: str | None,
        y_column: str | None,
        x_columns: list[str],
    ) -> int:
        state = dataset.get_state()
        manager = DuckDBManager()
        return manager.save_analysis_state(
            name=name,
            dataset=state["base_table"],
            filters=state["filters"],
            order_by=state["ordering"],
            selected_columns=state["selected_columns"],
            model_type=model_type,
            y=y_column,
            x=x_columns,
        )

    def list_analyses(self) -> list[dict]:
        manager = DuckDBManager()
        return manager.list_analysis_states()

    def load_analysis(self, analysis_id: int) -> tuple[DatasetModel, dict]:
        manager = DuckDBManager()
        state = manager.get_analysis_state(analysis_id)
        if state is None:
            raise ValueError("La sesión seleccionada no existe.")

        dataset_state = {
            "base_table": state["dataset"],
            "path": "",
            "filters": state["filters"],
            "ordering": state["order_by"],
            "selected_columns": state["selected_columns"],
        }
        dataset = Dataset.from_state(manager.connection, dataset_state)
        return DatasetModel(dataset=dataset), state

    def list_analysis_names(self) -> list[str]:
        manager = DuckDBManager()
        return manager.list_analysis_names()

    def list_versions(self, analysis_name: str) -> list[dict]:
        manager = DuckDBManager()
        return manager.list_analysis_versions(analysis_name)

    def get_version(self, version_id: int) -> dict | None:
        manager = DuckDBManager()
        return manager.get_analysis_version(version_id)

    def load_version(self, version_id: int) -> tuple[DatasetModel, dict]:
        manager = DuckDBManager()
        state = manager.get_analysis_version(version_id)
        if state is None:
            raise ValueError("La version seleccionada no existe.")
        dataset_state = {
            "base_table": state["dataset"],
            "path": "",
            "filters": state["filters"],
            "ordering": state["order_by"],
            "selected_columns": state["selected_columns"],
        }
        dataset = Dataset.from_state(manager.connection, dataset_state)
        return DatasetModel(dataset=dataset), state

    def list_all_versions(self) -> list[dict]:
        manager = DuckDBManager()
        return manager.list_all_versions()

    def compare_states(self, state_a: dict, state_b: dict) -> dict:
        return compare_states(
            {
                "filters": state_a.get("filters", []),
                "order_by": state_a.get("order_by"),
                "selected_columns": state_a.get("selected_columns"),
                "dataset": state_a.get("dataset"),
            },
            {
                "filters": state_b.get("filters", []),
                "order_by": state_b.get("order_by"),
                "selected_columns": state_b.get("selected_columns"),
                "dataset": state_b.get("dataset"),
            },
        )

    def compare_datasets(self, dataset_a: DatasetModel, dataset_b: DatasetModel):
        return compare_datasets(
            shape_a=dataset_a.get_shape(),
            shape_b=dataset_b.get_shape(),
            columns_a=dataset_a.get_columns(),
            columns_b=dataset_b.get_columns(),
        )

    def compare_models(
        self,
        result_a,
        result_b,
        metrics_a: dict | None = None,
        metrics_b: dict | None = None,
    ):
        return compare_model_results(result_a, result_b, metrics_a=metrics_a, metrics_b=metrics_b)
