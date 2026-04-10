from __future__ import annotations

from desktop_app.models.dataset_model import DatasetModel
from src.core.database import DuckDBManager
from src.core.compare import compare_datasets, compare_states, compare_model_results
from src.core.dataset import Dataset
from src.core.evaluation import evaluar_clasificacion, evaluar_regresion
from src.core.loader import list_datasets, load_dataset, load_existing_dataset
from src.core.regression import run_logit, run_ols, run_probit


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

    def save_analysis_version(
        self,
        *,
        analysis_name: str,
        parent_version_id: int | None,
        branch: str,
        dataset: DatasetModel,
        model_type: str | None,
        y_column: str | None,
        x_columns: list[str],
    ) -> dict:
        state = dataset.get_state()
        manager = DuckDBManager()
        return manager.save_analysis_version(
            analysis_name=analysis_name,
            parent_version_id=parent_version_id,
            branch=branch,
            dataset=state["base_table"],
            filters=state["filters"],
            order_by=state["ordering"],
            selected_columns=state["selected_columns"],
            model_type=model_type,
            y=y_column,
            x=x_columns,
        )

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

    def compare_models(self, result_a, result_b, metrics_a: dict | None = None, metrics_b: dict | None = None):
        return compare_model_results(result_a, result_b, metrics_a=metrics_a, metrics_b=metrics_b)
