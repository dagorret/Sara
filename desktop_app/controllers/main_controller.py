from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from desktop_app.models.dataset_model import DatasetModel
from desktop_app.services.dataset_service import DatasetService
from desktop_app.views.main_window import MainWindow
from src.core.report import (
    construir_tabla_coeficientes,
    generate_interpretative_report,
    generate_technical_report,
)


class MainController:
    def __init__(
        self,
        view: MainWindow,
        dataset_service: DatasetService | None = None,
    ) -> None:
        self.view = view
        self.dataset_service = dataset_service or DatasetService()
        self.datasets: dict[str, DatasetModel] = {}
        self.dataset: DatasetModel | None = None
        self.current_page = 0
        self.page_size = 10
        self.total_rows = 0
        self.total_columns = 0
        self.current_sort: tuple[str, bool] | None = None
        self.current_model_type: str | None = None
        self.current_version_state: dict | None = None

        self.view.load_csv_requested.connect(self.load_csv)
        self.view.next_page_requested.connect(self.next_page)
        self.view.prev_page_requested.connect(self.prev_page)
        self.view.dataset_selected.connect(self.select_dataset)
        self.view.add_filter_requested.connect(self.add_filter)
        self.view.remove_filter_requested.connect(self.remove_filter)
        self.view.clear_filters_requested.connect(self.clear_filters)
        self.view.save_analysis_requested.connect(self.save_analysis)
        self.view.load_analysis_requested.connect(self.load_analysis)
        self.view.analysis_name_selected.connect(self.select_analysis_name)
        self.view.save_version_requested.connect(self.save_version)
        self.view.create_branch_requested.connect(self.create_branch)
        self.view.load_version_requested.connect(self.load_version)
        self.view.compare_versions_requested.connect(self.compare_versions)
        self.view.apply_visible_columns_requested.connect(self.apply_visible_columns)
        self.view.run_ols_requested.connect(self.run_ols)
        self.view.run_logit_requested.connect(self.run_logit)
        self.view.run_probit_requested.connect(self.run_probit)
        self.view.table_view.horizontalHeader().sectionClicked.connect(
            self.sort_by_column_index
        )
        self.view.set_empty_state()
        self._load_persisted_datasets()
        self._refresh_analysis_options()
        self._refresh_version_options()
        self._refresh_compare_version_options()

    def load_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Seleccionar archivo CSV",
            "",
            "CSV files (*.csv);;All files (*)",
        )

        if not file_path:
            return

        try:
            dataset = self.dataset_service.load_dataset(file_path)
        except Exception as error:
            QMessageBox.critical(
                self.view,
                "Error al cargar CSV",
                f"No se pudo cargar el archivo seleccionado.\n\n{error}",
            )
            return

        self.datasets[dataset.table_name] = dataset
        self.view.add_dataset_option(dataset.table_name)
        self.view.set_selected_dataset(dataset.table_name)
        self._activate_dataset(dataset)

    def select_dataset(self, table_name: str) -> None:
        if not table_name:
            return

        dataset = self.datasets.get(table_name)
        if dataset is None:
            try:
                dataset = self.dataset_service.get_dataset(table_name)
            except Exception as error:
                QMessageBox.critical(
                    self.view,
                    "Error al activar dataset",
                    f"No se pudo abrir el dataset seleccionado.\n\n{error}",
                )
                return
            self.datasets[table_name] = dataset

        self._activate_dataset(dataset)

    def load_page(self, page: int) -> None:
        if self.dataset is None:
            return

        if self.total_rows == 0:
            self.current_page = 0
            self.view.set_table_data(None, offset=0)
            self.view.set_dataset_window(0, 0, 0, 0)
            self.view.set_pagination_enabled(has_previous=False, has_next=False)
            return

        max_page = max((self.total_rows - 1) // self.page_size, 0)
        target_page = min(max(page, 0), max_page)
        offset = target_page * self.page_size
        dataframe = self.dataset.get_page(limit=self.page_size, offset=offset)

        if dataframe.empty:
            return

        self.current_page = target_page
        self.view.set_table_data(dataframe, offset=offset)
        start_row = offset
        end_row = offset + len(dataframe.index) - 1
        self.view.set_dataset_window(
            start_row=start_row,
            end_row=end_row,
            total_rows=self.total_rows,
            page_number=self.current_page + 1,
        )
        has_previous = self.current_page > 0
        has_next = self.current_page < max_page
        self.view.set_pagination_enabled(
            has_previous=has_previous,
            has_next=has_next,
        )

    def next_page(self) -> None:
        self.load_page(self.current_page + 1)

    def prev_page(self) -> None:
        if self.current_page == 0:
            return
        self.load_page(self.current_page - 1)

    def _render_dataset(self) -> None:
        if self.dataset is None:
            return

        file_name = Path(self.dataset.path).name if self.dataset.path else self.dataset.table_name
        state = self.dataset.get_state()
        selected_columns = state["selected_columns"] or self.dataset.get_columns()
        filters_count = len(state["filters"])
        order_text = "sin orden"
        ordering = state["ordering"]
        if ordering:
            direction = "ASC" if ordering["ascending"] else "DESC"
            order_text = f"{ordering['column']} {direction}"
        self.view.show_dataset_info(
            dataset_name=self.dataset.table_name,
            file_name=file_name,
            total_rows=self.total_rows,
            total_columns=self.total_columns,
            filters_count=filters_count,
            order_text=order_text,
        )
        self.view.show_table_context(
            f"Archivo: {file_name} | Dataset: {self.dataset.table_name} | "
            f"Filas: {self.total_rows:,} | Columnas visibles: {len(selected_columns):,} | "
            f"Filtros: {filters_count} | Orden: {order_text}"
        )
        self.view.set_columns_metadata(self.dataset.get_columns_metadata())
        self.view.set_variable_options(self.dataset.get_base_columns())
        if state["selected_columns"]:
            self.view.set_selected_visible_columns(state["selected_columns"])
        self.view.set_active_filters(state["filters"])
        self.view.clear_model_results()
        self.view.set_model_status(
            f"Dataset activo: {self.dataset.table_name} ({self.total_rows:,} filas)"
        )
        self.load_page(0)

    def run_ols(self) -> None:
        self._run_model("OLS", self.dataset_service.run_ols)

    def run_logit(self) -> None:
        self._run_model("Logit", self.dataset_service.run_logit)

    def run_probit(self) -> None:
        self._run_model("Probit", self.dataset_service.run_probit)

    def _load_persisted_datasets(self) -> None:
        for table_name in self.dataset_service.list_datasets():
            self.view.add_dataset_option(table_name)

    def _activate_dataset(self, dataset: DatasetModel) -> None:
        self.dataset = dataset
        ordering = dataset.get_state().get("ordering")
        self.current_sort = None
        if ordering:
            self.current_sort = (ordering["column"], bool(ordering["ascending"]))
        self.current_page = 0
        self.total_rows, self.total_columns = dataset.get_shape()
        self.current_version_state = None
        self._render_dataset()

    def add_filter(self) -> None:
        if self.dataset is None:
            return

        column = self.view.get_selected_filter_column()
        operator = self.view.get_selected_filter_operator()
        raw_value = self.view.get_filter_text()
        if not column or not operator or raw_value == "":
            return

        condition = self._build_filter_condition(column, operator, raw_value)

        try:
            updated_dataset = self.dataset.filter(condition)
            updated_dataset.get_preview(1)
        except Exception as error:
            QMessageBox.critical(
                self.view,
                "Filtro inválido",
                f"No se pudo aplicar el filtro solicitado.\n\n{error}",
            )
            return

        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)

    def remove_filter(self) -> None:
        if self.dataset is None:
            return

        filter_index = self.view.get_selected_filter_index()
        if filter_index < 0:
            return

        state = self.dataset.get_state()
        filters = list(state["filters"])
        if filter_index >= len(filters):
            return
        filters.pop(filter_index)
        updated_dataset = self._rebuild_dataset_from_state(
            self.dataset,
            filters=filters,
        )
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)

    def clear_filters(self) -> None:
        if self.dataset is None:
            return
        updated_dataset = self._rebuild_dataset_from_state(self.dataset, filters=[])
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)

    def apply_visible_columns(self) -> None:
        if self.dataset is None:
            return

        selected_columns = self.view.get_selected_visible_columns()
        updated_dataset = self._rebuild_dataset_from_state(
            self.dataset,
            selected_columns=selected_columns or None,
        )
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)

    def sort_by_column_index(self, section: int) -> None:
        if self.dataset is None:
            return

        columns = self.dataset.get_columns()
        if section < 0 or section >= len(columns):
            return

        column_name = columns[section]
        ascending = True
        if self.current_sort and self.current_sort[0] == column_name:
            ascending = not self.current_sort[1]

        updated_dataset = self.dataset.order_by(column_name, ascending=ascending)
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)
        self.current_sort = (column_name, ascending)

    def _run_model(self, model_name: str, runner) -> None:
        if self.dataset is None:
            QMessageBox.warning(self.view, "Sin dataset", "Cargá o seleccioná un dataset primero.")
            return

        y_column = self.view.get_selected_y()
        x_columns = self.view.get_selected_x()

        if not y_column:
            QMessageBox.warning(self.view, "Variable dependiente", "Seleccioná una variable dependiente.")
            return

        if not x_columns:
            QMessageBox.warning(self.view, "Variables independientes", "Seleccioná al menos una variable independiente.")
            return

        if y_column in x_columns:
            QMessageBox.warning(
                self.view,
                "Selección inválida",
                "La variable dependiente no puede estar incluida entre las independientes.",
            )
            return

        try:
            result, messages = runner(self.dataset, y_column, x_columns)
        except Exception as error:
            QMessageBox.critical(
                self.view,
                f"Error al ejecutar {model_name}",
                f"No se pudo ejecutar el modelo.\n\n{error}",
            )
            return

        method = model_name.lower()
        metrics = self.dataset_service.build_model_metrics(
            result,
            self.dataset,
            {
                "model_type": method,
                "y": y_column,
                "x": x_columns,
            },
        )
        coefficients = construir_tabla_coeficientes(result)[
            ["Variable", "Coeficiente", "Valor p"]
        ].rename(columns={"Coeficiente": "Coef", "Valor p": "p-value"})
        interpretation = generate_interpretative_report(result, metrics=metrics, method=method)
        report = generate_technical_report(result, metrics=metrics, method=method)
        if messages:
            report = report + "\n\n=== ADVERTENCIAS ===\n" + "\n".join(
                f" - {message}" for message in messages
            )

        self.view.show_model_summary(
            model_name=model_name,
            formula=f"{y_column} ~ {' + '.join(x_columns)}",
            observations=int(result.nobs),
            status="Completado" if not messages else "Completado con advertencias",
        )
        self.view.show_metrics(self._build_metrics_panel(result, metrics))
        self.view.show_coefficients(coefficients)
        self.view.show_interpretation(interpretation)
        self.view.show_report(report)
        self.view.set_model_status(
            f"{model_name} ejecutado: {y_column} ~ {' + '.join(x_columns)} "
            f"({int(result.nobs):,} filas)"
        )
        self.current_model_type = method

    def save_analysis(self) -> None:
        if self.dataset is None:
            QMessageBox.warning(self.view, "Sin dataset", "No hay un analisis activo para guardar.")
            return

        default_name = f"Analisis {self.dataset.table_name}"
        name, accepted = QInputDialog.getText(
            self.view,
            "Guardar analisis",
            "Nombre de la sesion:",
            text=default_name,
        )
        if not accepted or not name.strip():
            return

        analysis_id = self.dataset_service.save_analysis(
            name=name.strip(),
            dataset=self.dataset,
            model_type=self.current_model_type,
            y_column=self.view.get_selected_y() or None,
            x_columns=self.view.get_selected_x(),
        )
        self._refresh_analysis_options()
        self.view.set_model_status(
            f"Analisis guardado: {name.strip()} (id={analysis_id})"
        )
        self._refresh_version_options()
        self._refresh_compare_version_options()

    def load_analysis(self) -> None:
        analysis_id = self.view.get_selected_analysis_id()
        if analysis_id is None:
            return

        try:
            dataset, state = self.dataset_service.load_analysis(analysis_id)
        except Exception as error:
            QMessageBox.critical(
                self.view,
                "Error al cargar analisis",
                f"No se pudo reconstruir la sesion seleccionada.\n\n{error}",
            )
            return

        self.datasets[dataset.table_name] = dataset
        self.view.add_dataset_option(dataset.table_name)
        self.view.set_selected_dataset(dataset.table_name)
        self._activate_dataset(dataset)
        if state.get("y"):
            self.view.set_selected_y(state["y"])
        self.view.set_selected_x(state.get("x", []))
        self.view.set_model_status(
            f"Analisis cargado: {state['name']} [{state['dataset']}]"
        )
        self.current_model_type = state.get("model_type")
        self.current_version_state = None
        self._refresh_version_options()
        self._refresh_compare_version_options()

    def select_analysis_name(self, analysis_name: str) -> None:
        if not analysis_name:
            self.view.set_version_options([])
            return
        self._refresh_version_options(analysis_name)

    def save_version(self) -> None:
        if self.dataset is None:
            QMessageBox.warning(self.view, "Sin dataset", "No hay analisis activo para versionar.")
            return

        default_name = self.view.get_selected_analysis_name() or f"Analisis {self.dataset.table_name}"
        analysis_name, accepted = QInputDialog.getText(
            self.view,
            "Nueva version",
            "Nombre del analisis:",
            text=default_name,
        )
        if not accepted or not analysis_name.strip():
            return

        parent_version_id = self._get_selected_or_current_version_id()
        branch_name = self._get_active_branch()
        version_info = self.dataset_service.save_analysis_version(
            analysis_name=analysis_name.strip(),
            parent_version_id=parent_version_id,
            branch=branch_name,
            dataset=self.dataset,
            model_type=self.current_model_type,
            y_column=self.view.get_selected_y() or None,
            x_columns=self.view.get_selected_x(),
        )
        self.current_version_state = self.dataset_service.get_version(version_info["id"])
        self._refresh_analysis_options()
        self.view.set_analysis_name_options(self.dataset_service.list_analysis_names())
        self._refresh_version_options(analysis_name.strip())
        self.view.set_selected_version(version_info["id"])
        self.view.set_model_status(
            f"Version guardada: {analysis_name.strip()} [{version_info['branch']}] v{version_info['version']}"
        )
        self._refresh_compare_version_options()

    def create_branch(self) -> None:
        if self.dataset is None:
            QMessageBox.warning(self.view, "Sin dataset", "No hay analisis activo para ramificar.")
            return

        base_version_id = self._get_selected_or_current_version_id()
        if base_version_id is None:
            QMessageBox.warning(
                self.view,
                "Sin version base",
                "Seleccioná o cargá una version para crear una rama.",
            )
            return

        base_state = self.dataset_service.get_version(base_version_id)
        if base_state is None:
            QMessageBox.warning(
                self.view,
                "Version inválida",
                "No se pudo resolver la version base seleccionada.",
            )
            return

        default_branch = f"{base_state.get('branch') or 'main'}_experimento"
        branch_name, accepted = QInputDialog.getText(
            self.view,
            "Crear rama",
            "Nombre de la nueva rama:",
            text=default_branch,
        )
        if not accepted or not branch_name.strip():
            return

        analysis_name = self.view.get_selected_analysis_name() or base_state["analysis_name"]
        version_info = self.dataset_service.save_analysis_version(
            analysis_name=analysis_name,
            parent_version_id=base_version_id,
            branch=branch_name.strip(),
            dataset=self.dataset,
            model_type=self.current_model_type,
            y_column=self.view.get_selected_y() or None,
            x_columns=self.view.get_selected_x(),
        )
        self.current_version_state = self.dataset_service.get_version(version_info["id"])
        self._refresh_analysis_options()
        self._refresh_version_options(analysis_name)
        self.view.set_selected_version(version_info["id"])
        self._refresh_compare_version_options()
        self.view.set_model_status(
            "Rama creada: "
            f"{analysis_name} [{version_info['branch']}] v{version_info['version']}"
        )

    def load_version(self) -> None:
        version_id = self.view.get_selected_version_id()
        if version_id is None:
            return

        try:
            dataset, state = self.dataset_service.load_version(version_id)
        except Exception as error:
            QMessageBox.critical(
                self.view,
                "Error al cargar version",
                f"No se pudo reconstruir la version seleccionada.\n\n{error}",
            )
            return

        self.datasets[dataset.table_name] = dataset
        self.view.add_dataset_option(dataset.table_name)
        self.view.set_selected_dataset(dataset.table_name)
        self._activate_dataset(dataset)
        if state.get("y"):
            self.view.set_selected_y(state["y"])
        self.view.set_selected_x(state.get("x", []))
        self.view.set_analysis_name_options(self.dataset_service.list_analysis_names())
        self._refresh_version_options(state["analysis_name"])
        self.view.set_selected_version(state["id"])
        diff_text = self._build_version_diff_text(state)
        self.view.set_model_status(
            f"Version cargada: {state['analysis_name']} [{state.get('branch') or 'main'}] v{state['version']}"
        )
        self.current_model_type = state.get("model_type")
        self.current_version_state = state
        if diff_text:
            self.view.set_results_text(diff_text)
        self._refresh_compare_version_options()

    def compare_versions(self) -> None:
        version_a_id, version_b_id = self.view.get_compare_version_ids()
        if version_a_id is None or version_b_id is None:
            return

        dataset_a, state_a = self.dataset_service.load_version(version_a_id)
        dataset_b, state_b = self.dataset_service.load_version(version_b_id)

        summary_lines = [
            f"Comparacion A/B: {state_a['analysis_name']} v{state_a['version']} vs "
            f"{state_b['analysis_name']} v{state_b['version']}",
        ]
        comparison_tables = []

        state_diff = self.dataset_service.compare_states(state_a, state_b)
        if not state_diff["table"].empty:
            comparison_tables.append(state_diff["table"])
        summary_lines.extend(state_diff["summary"])

        dataset_df, dataset_summary = self.dataset_service.compare_datasets(dataset_a, dataset_b)
        if not dataset_df.empty:
            comparison_tables.append(dataset_df)
        summary_lines.extend(dataset_summary)

        if self._can_compare_models(state_a, state_b):
            result_a = self._run_model_for_state(dataset_a, state_a)
            result_b = self._run_model_for_state(dataset_b, state_b)
            if result_a is not None and result_b is not None:
                metrics_a = self.dataset_service.build_model_metrics(result_a, dataset_a, state_a)
                metrics_b = self.dataset_service.build_model_metrics(result_b, dataset_b, state_b)
                compare_df, model_summary = self.dataset_service.compare_models(
                    result_a,
                    result_b,
                    metrics_a=metrics_a,
                    metrics_b=metrics_b,
                )
                if not compare_df.empty:
                    comparison_tables.append(compare_df)
                summary_lines.extend(model_summary)

        if len(summary_lines) == 1:
            summary_lines.append("No se detectaron diferencias relevantes entre ambos estados.")

        compare_df = (
            pd.concat(comparison_tables, ignore_index=True)
            if comparison_tables
            else pd.DataFrame(columns=["Categoria", "Elemento", "Modelo A", "Modelo B", "Diferencia"])
        )
        self.view.set_compare_results("\n".join(summary_lines), compare_df)

    def _format_model_output(
        self,
        model_name: str,
        y_column: str,
        x_columns: list[str],
        result,
        messages: list[str],
    ) -> str:
        lines = [
            f"{model_name} ejecutado: {y_column} ~ {' + '.join(x_columns)}",
            f"Observaciones: {int(result.nobs):,}",
        ]

        if hasattr(result, "rsquared"):
            lines.append(f"R-cuadrado: {float(result.rsquared):.4f}")
            lines.append(f"R-cuadrado ajustado: {float(result.rsquared_adj):.4f}")

        if hasattr(result, "llf"):
            lines.append(f"Log-likelihood: {float(result.llf):.4f}")

        lines.append("")
        lines.append("Coeficientes:")
        for variable in result.params.index:
            lines.append(
                f" - {variable}: coef={float(result.params[variable]):.4f}, "
                f"se={float(result.bse[variable]):.4f}, "
                f"p={float(result.pvalues[variable]):.4f}"
            )

        if messages:
            lines.append("")
            lines.append("Advertencias:")
            for message in messages:
                lines.append(f" - {message}")

        return "\n".join(lines)

    def _refresh_analysis_options(self) -> None:
        self.view.set_analysis_options(self.dataset_service.list_analyses())
        self.view.set_analysis_name_options(self.dataset_service.list_analysis_names())

    def _refresh_version_options(self, analysis_name: str | None = None) -> None:
        selected_name = analysis_name or self.view.get_selected_analysis_name()
        if not selected_name:
            self.view.set_version_options([])
            return
        self.view.set_version_options(self.dataset_service.list_versions(selected_name))

    def _refresh_compare_version_options(self) -> None:
        self.view.set_compare_version_options(self.dataset_service.list_all_versions())

    @staticmethod
    def _build_metrics_panel(result, metrics: dict) -> dict:
        panel = {
            "Observaciones": int(result.nobs),
        }
        if hasattr(result, "rsquared"):
            panel["R-cuadrado"] = float(result.rsquared)
            panel["R-cuadrado ajustado"] = float(result.rsquared_adj)
        if hasattr(result, "prsquared"):
            panel["Pseudo R-cuadrado"] = float(result.prsquared)
        if hasattr(result, "llf"):
            panel["Log-likelihood"] = float(result.llf)

        for source_key, target_label in (
            ("accuracy", "Accuracy"),
            ("auc", "AUC"),
            ("precision", "Precision"),
            ("recall", "Recall"),
            ("f1", "F1"),
            ("threshold", "Threshold"),
        ):
            if source_key in metrics:
                panel[target_label] = metrics[source_key]
        return panel

    def _build_filter_condition(self, column: str, operator: str, raw_value: str) -> str:
        normalized_value = raw_value.strip()
        upper_value = normalized_value.upper()
        if operator == "LIKE":
            value_sql = self._quote_sql_string(normalized_value)
        elif upper_value == "NULL":
            value_sql = "NULL"
        else:
            try:
                float(normalized_value)
                value_sql = normalized_value
            except ValueError:
                value_sql = self._quote_sql_string(normalized_value)
        return f'"{column}" {operator} {value_sql}'

    @staticmethod
    def _quote_sql_string(value: str) -> str:
        return "'" + value.replace("'", "''") + "'"

    def _rebuild_dataset_from_state(
        self,
        dataset: DatasetModel,
        *,
        filters: list[str] | None = None,
        ordering: dict | None = None,
        selected_columns: list[str] | None | object = None,
    ) -> DatasetModel:
        state = dataset.get_state()
        next_state = {
            "base_table": state["base_table"],
            "path": state["path"],
            "filters": state["filters"] if filters is None else filters,
            "ordering": state["ordering"] if ordering is None else ordering,
            "selected_columns": state["selected_columns"],
        }
        if selected_columns is not None:
            next_state["selected_columns"] = selected_columns
        rebuilt = DatasetModel(
            dataset=dataset.dataset.from_state(dataset.dataset.connection, next_state)
        )
        return rebuilt

    def _build_version_diff_text(self, version_state: dict) -> str:
        parent_id = version_state.get("parent_version")
        if not parent_id:
            return (
                f"Historial: {version_state['analysis_name']} v{version_state['version']}\n"
                "Sin version anterior para comparar."
            )

        parent_dataset, parent_state = self.dataset_service.load_version(parent_id)
        del parent_dataset

        current_filters = set(version_state.get("filters", []))
        parent_filters = set(parent_state.get("filters", []))
        added_filters = sorted(current_filters - parent_filters)
        removed_filters = sorted(parent_filters - current_filters)

        lines = [
            f"Historial: {version_state['analysis_name']} v{version_state['version']}",
            f"Rama: {version_state.get('branch') or 'main'}",
            f"Comparado contra v{parent_state['version']}",
        ]

        if version_state.get("branch") != parent_state.get("branch"):
            lines.append(
                f"Rama: {parent_state.get('branch') or 'main'} -> {version_state.get('branch') or 'main'}"
            )

        if added_filters:
            lines.append("Filtros agregados:")
            for item in added_filters:
                lines.append(f" - {item}")

        if removed_filters:
            lines.append("Filtros removidos:")
            for item in removed_filters:
                lines.append(f" - {item}")

        if version_state.get("order_by") != parent_state.get("order_by"):
            lines.append(
                f"Orden: {parent_state.get('order_by')} -> {version_state.get('order_by')}"
            )

        if version_state.get("selected_columns") != parent_state.get("selected_columns"):
            lines.append(
                "Columnas visibles: "
                f"{parent_state.get('selected_columns')} -> {version_state.get('selected_columns')}"
            )

        if version_state.get("y") != parent_state.get("y") or version_state.get("x") != parent_state.get("x"):
            lines.append(
                f"Modelo: y={parent_state.get('y')}, x={parent_state.get('x')} -> "
                f"y={version_state.get('y')}, x={version_state.get('x')}"
            )

        return "\n".join(lines)

    def _can_compare_models(self, state_a: dict, state_b: dict) -> bool:
        return bool(
            state_a.get("model_type")
            and state_b.get("model_type")
            and state_a.get("model_type") == state_b.get("model_type")
            and state_a.get("y")
            and state_b.get("y")
            and state_a.get("x")
            and state_b.get("x")
        )

    def _run_model_for_state(self, dataset: DatasetModel, state: dict):
        y = state.get("y")
        x = state.get("x", [])
        if not y or not x:
            return None
        if set(x) == set() or y in x:
            return None

        method = (state.get("model_type") or "ols").lower()
        if method == "logit":
            result, _ = self.dataset_service.run_logit(dataset, y, x)
        elif method == "probit":
            result, _ = self.dataset_service.run_probit(dataset, y, x)
        else:
            result, _ = self.dataset_service.run_ols(dataset, y, x)
        return result

    def _get_selected_or_current_version_id(self) -> int | None:
        selected_version_id = self.view.get_selected_version_id()
        if selected_version_id is not None:
            return selected_version_id
        if self.current_version_state is not None:
            version_id = self.current_version_state.get("id")
            if version_id is not None:
                return int(version_id)
        return None

    def _get_active_branch(self) -> str:
        if self.current_version_state and self.current_version_state.get("branch"):
            return str(self.current_version_state["branch"])

        selected_version_id = self.view.get_selected_version_id()
        if selected_version_id is not None:
            state = self.dataset_service.get_version(selected_version_id)
            if state and state.get("branch"):
                return str(state["branch"])

        return "main"
