from __future__ import annotations

import logging
from pathlib import Path
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog

from desktop_app.models.dataset_model import DatasetModel
from desktop_app.services.dataset_service import DatasetService
from desktop_app.views.main_window import MainWindow
from src.core.config import DEFAULT_PAGE_SIZE
from src.core.exceptions import ModelError, QueryError, ValidationError


log = logging.getLogger(__name__)


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
        self.page_size = DEFAULT_PAGE_SIZE
        self.total_rows = 0
        self.total_columns = 0
        self.current_sort: tuple[str, bool] | None = None
        self.current_model_type: str | None = None
        self.current_result = None
        self.current_metrics: dict = {}
        self.current_reports: dict[str, str] = {}
        self.current_coefficients = None
        self.current_formula: str | None = None
        self.current_execution_signature: str | None = None

        self._connect_signals()
        self._attach_log_handler()
        self.view.set_empty_state()
        self._load_persisted_datasets()

    def _connect_signals(self) -> None:
        self.view.load_csv_requested.connect(self.load_csv)
        self.view.save_analysis_requested.connect(self.save_analysis)
        self.view.load_analysis_requested.connect(self.load_analysis)
        self.view.exit_requested.connect(self.view.close)
        self.view.show_metadata_requested.connect(self.show_metadata)
        self.view.clear_filters_requested.connect(self.clear_filters)
        self.view.next_page_requested.connect(self.next_page)
        self.view.prev_page_requested.connect(self.prev_page)
        self.view.dataset_selected.connect(self.select_dataset)
        self.view.add_filter_requested.connect(self.add_filter)
        self.view.remove_filter_requested.connect(self.remove_filter)
        self.view.run_ols_requested.connect(self.run_ols)
        self.view.run_logit_requested.connect(self.run_logit)
        self.view.run_probit_requested.connect(self.run_probit)
        self.view.show_simple_report_requested.connect(
            lambda: self.show_cached_report("simple", "Reporte simple")
        )
        self.view.show_technical_report_requested.connect(
            lambda: self.show_cached_report("technical", "Reporte técnico")
        )
        self.view.show_interpretative_report_requested.connect(
            lambda: self.show_cached_report("interpretative", "Reporte interpretativo")
        )
        self.view.export_txt_requested.connect(self.export_txt)
        self.view.export_csv_requested.connect(self.export_csv)
        self.view.copy_report_requested.connect(self.copy_report)
        self.view.copy_full_report_requested.connect(self.copy_full_report)
        self.view.export_full_report_requested.connect(self.export_full_report)
        self.view.show_logs_requested.connect(self.show_logs)
        self.view.show_settings_requested.connect(self.show_settings_placeholder)
        self.view.variable_selection_changed.connect(self._update_analysis_state)
        self.view.table_view.horizontalHeader().sectionClicked.connect(
            self.sort_by_column_index
        )

    def _attach_log_handler(self) -> None:
        handler = self.view.get_log_handler()
        root_logger = logging.getLogger()
        if handler not in root_logger.handlers:
            root_logger.addHandler(handler)
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)

    def _load_persisted_datasets(self) -> None:
        for table_name in self.dataset_service.list_datasets():
            self.view.add_dataset_option(table_name)

    def load_csv(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Seleccionar dataset CSV",
            "",
            "CSV files (*.csv);;All files (*)",
        )
        if not file_path:
            return

        try:
            dataset = self.dataset_service.load_dataset(file_path)
        except Exception as error:
            log.exception("Could not load CSV: %s", file_path)
            self.view.show_feedback(
                f"No se pudo cargar el dataset seleccionado: {error}",
                error=True,
            )
            return

        self.datasets[dataset.table_name] = dataset
        self.view.add_dataset_option(dataset.table_name)
        self.view.set_selected_dataset(dataset.table_name)
        self._activate_dataset(dataset)
        self.view.show_feedback(
            f"Dataset cargado: {dataset.table_name} ({Path(file_path).name})"
        )

    def select_dataset(self, table_name: str) -> None:
        if not table_name:
            return

        dataset = self.datasets.get(table_name)
        if dataset is None:
            try:
                dataset = self.dataset_service.get_dataset(table_name)
            except Exception as error:
                log.exception("Could not activate dataset '%s'", table_name)
                self.view.show_feedback(
                    f"No se pudo abrir el dataset '{table_name}': {error}",
                    error=True,
                )
                return
            self.datasets[table_name] = dataset

        self._activate_dataset(dataset)
        self.view.show_feedback(f"Dataset activo: {table_name}")

    def _activate_dataset(self, dataset: DatasetModel) -> None:
        self.dataset = dataset
        self.current_page = 0
        state = dataset.get_state()
        ordering = state.get("ordering")
        self.current_sort = None
        if ordering:
            self.current_sort = (ordering["column"], bool(ordering["ascending"]))
        self.total_rows, self.total_columns = dataset.get_shape()
        self._render_dataset()
        self.view.set_has_dataset(True)
        self._update_analysis_state()

    def _render_dataset(self) -> None:
        if self.dataset is None:
            return

        state = self.dataset.get_state()
        order_text = "sin orden"
        if state.get("ordering"):
            direction = "ASC" if state["ordering"]["ascending"] else "DESC"
            order_text = f"{state['ordering']['column']} {direction}"

        self.view.show_dataset_info(
            dataset_name=self.dataset.table_name,
            total_rows=self.total_rows,
            total_columns=self.total_columns,
            filters_count=len(state["filters"]),
        )
        self.view.set_variable_options(self.dataset.get_base_columns())
        self.view.set_active_filters(state["filters"])
        self.load_page(0, order_text=order_text)
        self._update_analysis_state()

    def load_page(self, page: int, *, order_text: str | None = None) -> None:
        if self.dataset is None:
            return

        if self.total_rows == 0:
            self.view.show_table(None)
            self.view.show_table_context(
                start_row=0,
                end_row=0,
                total_rows=0,
                filters_count=len(self.dataset.get_state()["filters"]),
                order_text=order_text or "sin orden",
                page_number=0,
                total_pages=0,
            )
            self.view.set_pagination_enabled(has_previous=False, has_next=False)
            return

        max_page = max((self.total_rows - 1) // self.page_size, 0)
        target_page = min(max(page, 0), max_page)
        offset = target_page * self.page_size
        try:
            dataframe = self.dataset.get_page(limit=self.page_size, offset=offset)
        except (ValidationError, QueryError) as error:
            self._present_error("Error al cargar página", error)
            return
        self.current_page = target_page

        current_order = order_text
        if current_order is None:
            ordering = self.dataset.get_state().get("ordering")
            if ordering:
                direction = "ASC" if ordering["ascending"] else "DESC"
                current_order = f"{ordering['column']} {direction}"
            else:
                current_order = "sin orden"

        start_row = offset + 1 if len(dataframe.index) > 0 else 0
        end_row = offset + len(dataframe.index)
        total_pages = max_page + 1

        self.view.show_table(dataframe, offset=offset)
        self.view.show_table_context(
            start_row=start_row,
            end_row=end_row,
            total_rows=self.total_rows,
            filters_count=len(self.dataset.get_state()["filters"]),
            order_text=current_order,
            page_number=self.current_page + 1,
            total_pages=total_pages,
        )
        self.view.set_pagination_enabled(
            has_previous=self.current_page > 0,
            has_next=self.current_page < max_page,
        )

    def next_page(self) -> None:
        self.load_page(self.current_page + 1)

    def prev_page(self) -> None:
        self.load_page(self.current_page - 1)

    def add_filter(self) -> None:
        if self.dataset is None:
            self.view.show_feedback("Seleccioná un dataset antes de filtrar.", error=True)
            return

        column = self.view.get_selected_filter_column()
        operator = self.view.get_selected_filter_operator()
        raw_value = self.view.get_filter_text()
        if not column or not operator or raw_value == "":
            self.view.show_feedback("Completá columna, operador y valor para agregar el filtro.", error=True)
            return

        condition = self._build_filter_condition(column, operator, raw_value)
        try:
            updated_dataset = self.dataset.filter(condition)
            updated_dataset.get_preview(1)
        except Exception as error:
            log.exception("Invalid filter '%s'", condition)
            self.view.show_feedback(f"No se pudo aplicar el filtro: {error}", error=True)
            return

        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)
        self.view.clear_filter_input()
        self.view.show_feedback(f"Filtro aplicado: {condition}")

    def remove_filter(self) -> None:
        if self.dataset is None:
            return

        selected_index = self.view.get_selected_filter_index()
        if selected_index < 0:
            self.view.show_feedback("Seleccioná un filtro activo para quitarlo.", error=True)
            return

        state = self.dataset.get_state()
        filters = list(state["filters"])
        if selected_index >= len(filters):
            return

        removed = filters.pop(selected_index)
        updated_dataset = self._rebuild_dataset_from_state(self.dataset, filters=filters)
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)
        self.view.show_feedback(f"Filtro removido: {removed}")

    def clear_filters(self) -> None:
        if self.dataset is None:
            return

        updated_dataset = self._rebuild_dataset_from_state(self.dataset, filters=[])
        self.datasets[updated_dataset.table_name] = updated_dataset
        self._activate_dataset(updated_dataset)
        self.view.show_feedback("Filtros reseteados.")

    def show_metadata(self) -> None:
        if self.dataset is None:
            self.view.show_feedback("Seleccioná un dataset antes de ver metadata.", error=True)
            return

        try:
            metadata = self.dataset_service.get_metadata(self.dataset)
        except (ValidationError, QueryError) as error:
            self._present_error("Error al obtener metadata", error)
            return
        markdown = self._metadata_to_markdown(metadata)
        self.view.show_report(markdown, title="Reporte principal: metadata del dataset")
        self.view.show_full_report(markdown)
        self.view.focus_results("Reporte")
        self.view.show_feedback(f"Metadata visible para dataset '{self.dataset.table_name}'.")

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
        direction = "ASC" if ascending else "DESC"
        self.view.show_feedback(f"Orden aplicado: {column_name} {direction}")

    def run_ols(self) -> None:
        self._run_model("ols", "OLS", self.dataset_service.run_ols)

    def run_logit(self) -> None:
        self._run_model("logit", "Logit", self.dataset_service.run_logit)

    def run_probit(self) -> None:
        self._run_model("probit", "Probit", self.dataset_service.run_probit)

    def _run_model(self, method: str, label: str, runner) -> None:
        if self.dataset is None:
            self.view.show_feedback("Seleccioná un dataset antes de ejecutar un modelo.", error=True)
            return

        y_column = self.view.get_selected_y()
        x_columns = self.view.get_selected_x()

        if not y_column:
            self.view.show_feedback("Seleccioná la variable dependiente (Y).", error=True)
            return
        if not x_columns:
            self.view.show_feedback("Seleccioná al menos una variable explicativa (X).", error=True)
            return
        if y_column in x_columns:
            self.view.show_feedback(
                "La variable dependiente no puede estar incluida entre las independientes.",
                error=True,
            )
            return

        execution_signature = self._build_execution_signature(method, y_column, x_columns)
        if execution_signature == self.current_execution_signature:
            self.view.focus_results("Reporte")
            self.view.show_feedback(
                f"Resultado ya disponible para {label}: {y_column} ~ {' + '.join(x_columns)}"
            )
            return

        self.view.set_busy(True)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            result, messages = runner(self.dataset, y_column, x_columns)
        except (ValidationError, ModelError, QueryError) as error:
            self._present_error(f"Error al ejecutar {label}", error)
            return
        except Exception as error:
            log.exception("Model execution failed: %s", label)
            self.view.show_feedback(
                f"Error inesperado al ejecutar {label}: {error}",
                error=True,
            )
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.view.set_busy(False)

        metrics = self.dataset_service.build_model_metrics(
            result,
            self.dataset,
            {"model_type": method, "y": y_column, "x": x_columns},
        )
        coefficients = self.dataset_service.build_coefficients(result)
        reports = self.dataset_service.build_report_bundle(result, metrics, method)
        if messages:
            warnings_block = "\n".join(f"- {message}" for message in messages)
            reports["markdown"] += f"\n\n## Advertencias\n\n{warnings_block}"
            reports["technical"] += "\n\n=== ADVERTENCIAS ===\n" + "\n".join(
                f" - {message}" for message in messages
            )

        self.current_model_type = method
        self.current_result = result
        self.current_metrics = metrics
        self.current_reports = reports
        self.current_coefficients = coefficients
        self.current_formula = formula = f"{y_column} ~ {' + '.join(x_columns)}"
        self.current_execution_signature = execution_signature

        status = "Completado" if not messages else "Completado con advertencias"
        self.view.show_model_summary(
            {
                "model_name": label,
                "formula": formula,
                "observations": int(result.nobs),
                "status": status,
                "warnings": messages,
            }
        )
        self.view.show_metrics(self._build_metrics_panel(result, metrics))
        self.view.show_coefficients(coefficients)
        self.view.show_interpretation(reports["interpretative"])
        self.view.show_report(reports["markdown"], title="Reporte principal: markdown")
        self.view.show_full_report(reports["full_markdown"])
        self.view.show_latex(reports["latex"])
        self.view.focus_results("Reporte")
        self._update_analysis_state()
        self.view.show_feedback(
            f"✔ Modelo {label} ejecutado ({int(result.nobs):,} filas)"
        )
        log.info("Model %s executed successfully with formula %s", label, formula)

    def show_cached_report(self, key: str, title: str) -> None:
        if not self.current_reports:
            self.view.show_feedback("Ejecutá un modelo antes de abrir reportes.", error=True)
            return

        report_text = self.current_reports.get(key)
        if not report_text:
            self.view.show_feedback(f"No hay contenido disponible para {title.lower()}.", error=True)
            return

        self.view.show_report(report_text, title=f"Reporte principal: {title.lower()}")
        self.view.focus_results("Reporte")
        self.view.show_feedback(f"{title} visible en el panel de resultados.")

    def export_txt(self) -> None:
        if not self.current_reports:
            self.view.show_feedback("No hay reporte para exportar todavía.", error=True)
            return

        default_name = f"reporte_{self.current_model_type or 'modelo'}.txt"
        output_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Exportar reporte TXT",
            str(Path("resultados") / default_name),
            "Text files (*.txt);;Markdown (*.md);;All files (*)",
        )
        if not output_path:
            return

        try:
            path = self.dataset_service.export_report_text(self.current_reports["technical"], output_path)
        except Exception as error:
            log.exception("Could not export TXT report")
            self.view.show_feedback(f"No se pudo exportar el reporte: {error}", error=True)
            return

        self.view.show_feedback(f"Reporte exportado en {path}")

    def export_csv(self) -> None:
        if self.current_coefficients is None:
            self.view.show_feedback("No hay coeficientes para exportar todavía.", error=True)
            return

        default_name = f"coeficientes_{self.current_model_type or 'modelo'}.csv"
        output_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Exportar coeficientes CSV",
            str(Path("resultados") / default_name),
            "CSV files (*.csv);;All files (*)",
        )
        if not output_path:
            return

        try:
            path = self.dataset_service.export_coefficients_csv(self.current_coefficients, output_path)
        except Exception as error:
            log.exception("Could not export coefficients CSV")
            self.view.show_feedback(f"No se pudo exportar el CSV: {error}", error=True)
            return

        self.view.show_feedback(f"Coeficientes exportados en {path}")

    def copy_report(self) -> None:
        if not self.current_reports:
            self.view.show_feedback("No hay reporte para copiar todavía.", error=True)
            return
        QApplication.clipboard().setText(self.current_reports.get("markdown", ""))
        self.view.show_feedback("Reporte copiado al portapapeles.")

    def copy_full_report(self) -> None:
        if not self.current_reports:
            self.view.show_feedback("No hay reporte completo para copiar todavía.", error=True)
            return
        QApplication.clipboard().setText(self.current_reports.get("full_markdown", ""))
        self.view.show_feedback("Reporte completo copiado al portapapeles.")

    def export_full_report(self) -> None:
        if not self.current_reports:
            self.view.show_feedback("No hay reporte completo para exportar todavía.", error=True)
            return

        default_name = f"reporte_completo_{self.current_model_type or 'modelo'}.txt"
        output_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "Exportar reporte completo",
            str(Path("resultados") / default_name),
            "Text files (*.txt);;Markdown (*.md);;All files (*)",
        )
        if not output_path:
            return

        try:
            path = self.dataset_service.export_report_text(
                self.current_reports["full_markdown"],
                output_path,
            )
        except Exception as error:
            log.exception("Could not export full report")
            self.view.show_feedback(f"No se pudo exportar el reporte completo: {error}", error=True)
            return

        self.view.show_feedback(f"Reporte completo exportado en {path}")

    def save_analysis(self) -> None:
        if self.dataset is None:
            self.view.show_feedback("No hay análisis activo para guardar.", error=True)
            return

        default_name = f"Analisis {self.dataset.table_name}"
        name, accepted = QInputDialog.getText(
            self.view,
            "Guardar análisis",
            "Nombre del análisis:",
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
        self.view.show_feedback(f"Análisis guardado: {name.strip()} (id={analysis_id})")

    def load_analysis(self) -> None:
        analyses = self.dataset_service.list_analyses()
        if not analyses:
            self.view.show_feedback("No hay análisis guardados para cargar.", error=True)
            return

        labels = [f"{item['id']} | {item['name']} [{item['dataset']}]" for item in analyses]
        selected_label, accepted = QInputDialog.getItem(
            self.view,
            "Cargar análisis",
            "Seleccioná un análisis guardado:",
            labels,
            0,
            False,
        )
        if not accepted or not selected_label:
            return

        analysis_id = int(selected_label.split("|", 1)[0].strip())
        try:
            dataset, state = self.dataset_service.load_analysis(analysis_id)
        except Exception as error:
            log.exception("Could not load analysis id=%s", analysis_id)
            self.view.show_feedback(f"No se pudo cargar el análisis: {error}", error=True)
            return

        self.datasets[dataset.table_name] = dataset
        self.view.add_dataset_option(dataset.table_name)
        self.view.set_selected_dataset(dataset.table_name)
        self._activate_dataset(dataset)
        if state.get("y"):
            self.view.set_selected_y(state["y"])
        self.view.set_selected_x(state.get("x", []))
        self.current_model_type = state.get("model_type")
        self.current_formula = None
        self._update_analysis_state()
        self.view.show_feedback(f"Análisis cargado: {state['name']} [{state['dataset']}]")

    def show_logs(self) -> None:
        self.view.toggle_logs_panel()
        visibility = "visible" if self.view.log_dock.isVisible() else "oculto"
        self.view.show_feedback(f"Panel de logs {visibility}.")

    def show_settings_placeholder(self) -> None:
        self.view.show_feedback("Configuración todavía no implementada. Placeholder reservado.")

    def _reset_model_outputs(self) -> None:
        self.current_model_type = None
        self.current_result = None
        self.current_metrics = {}
        self.current_reports = {}
        self.current_coefficients = None
        self.current_formula = None
        self.current_execution_signature = None
        self._update_analysis_state()

    def _build_filter_condition(self, column: str, operator: str, raw_value: str) -> str:
        normalized_value = raw_value.strip()
        if normalized_value.upper() == "NULL":
            if operator == "=":
                return f"{column} IS NULL"
            if operator in {"!=", "<>"}:
                return f"{column} IS NOT NULL"

        try:
            float(normalized_value)
            value_sql = normalized_value
        except ValueError:
            escaped = normalized_value.replace("'", "''")
            value_sql = f"'{escaped}'"

        return f"{column} {operator} {value_sql}"

    def _rebuild_dataset_from_state(
        self,
        dataset: DatasetModel,
        *,
        filters: list[str] | None = None,
        ordering: dict | None = None,
    ) -> DatasetModel:
        state = dataset.get_state()
        next_state = {
            "base_table": state["base_table"],
            "path": state["path"],
            "filters": state["filters"] if filters is None else filters,
            "ordering": state["ordering"] if ordering is None else ordering,
            "selected_columns": state["selected_columns"],
        }
        return DatasetModel(
            dataset=dataset.dataset.from_state(dataset.dataset.connection, next_state)
        )

    def _update_analysis_state(self) -> None:
        dataset_name = self.dataset.table_name if self.dataset is not None else None
        filters = None
        if self.dataset is not None:
            filters = self.dataset.get_state().get("filters", [])

        model_name = None
        if self.current_model_type:
            model_name = self.current_model_type.upper() if self.current_model_type == "ols" else self.current_model_type.capitalize()

        self.view.show_analysis_state(
            dataset_name=dataset_name,
            filters=filters,
            model_name=model_name,
            y_column=self.view.get_selected_y() or None,
            x_columns=self.view.get_selected_x() or None,
        )
        self._update_empty_report_state()

    def _present_error(self, context: str, error: Exception) -> None:
        if isinstance(error, ValidationError):
            message = f"Error: {error}"
        elif isinstance(error, ModelError):
            message = f"Error del modelo: {error}"
        elif isinstance(error, QueryError):
            message = f"Error de consulta: {error}"
        else:
            message = f"{context}: {error}"
        log.exception("%s", context, exc_info=error)
        self.view.show_feedback(message, error=True)

    def _update_empty_report_state(self) -> None:
        if self.current_result is not None:
            return
        if self.dataset is None:
            self.view.show_report_empty_state("no_model")
            return
        y_column = self.view.get_selected_y()
        x_columns = self.view.get_selected_x()
        if not y_column or not x_columns:
            self.view.show_report_empty_state("missing_variables")
            return
        self.view.show_report_empty_state("ready")

    def _build_execution_signature(
        self,
        method: str,
        y_column: str,
        x_columns: list[str],
    ) -> str:
        dataset_state = self.dataset.get_state() if self.dataset is not None else {}
        payload = {
            "dataset": dataset_state.get("base_table"),
            "filters": dataset_state.get("filters", []),
            "ordering": dataset_state.get("ordering"),
            "selected_columns": dataset_state.get("selected_columns"),
            "method": method,
            "y": y_column,
            "x": list(x_columns),
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=True)

    @staticmethod
    def _build_metrics_panel(result, metrics: dict) -> dict[str, object]:
        panel: dict[str, object] = {"Observaciones": int(result.nobs)}
        if hasattr(result, "rsquared"):
            panel["R²"] = float(result.rsquared)
            panel["R² ajustado"] = float(result.rsquared_adj)
        if hasattr(result, "prsquared"):
            panel["Pseudo R²"] = float(result.prsquared)
        if hasattr(result, "llf"):
            panel["Log-likelihood"] = float(result.llf)
        for source_key, label in (
            ("accuracy", "Accuracy"),
            ("auc", "AUC"),
            ("precision", "Precision"),
            ("recall", "Recall"),
            ("f1", "F1"),
            ("threshold", "Threshold"),
        ):
            if source_key in metrics:
                panel[label] = metrics[source_key]
        return panel

    @staticmethod
    def _metadata_to_markdown(metadata: dict[str, object]) -> str:
        lines = [
            f"# Metadata del Dataset `{metadata['table']}`",
            "",
            f"- **Filas:** {metadata['rows']:,}",
            f"- **Columnas:** {len(metadata['columns']):,}",
            "",
            "## Columnas",
            "",
            "| Columna | Tipo | Nulos | Cardinalidad | Mean | Std |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]

        types = metadata["types"]
        null_counts = metadata["null_counts"]
        cardinality = metadata["cardinality"]
        stats = metadata["stats"]

        for column in metadata["columns"]:
            column_stats = stats[column]
            mean_value = "-" if column_stats["mean"] is None else f"{column_stats['mean']:.4f}"
            std_value = "-" if column_stats["std"] is None else f"{column_stats['std']:.4f}"
            lines.append(
                f"| {column} | {types[column]} | {null_counts[column]} | "
                f"{cardinality[column]} | {mean_value} | {std_value} |"
            )
        return "\n".join(lines)
