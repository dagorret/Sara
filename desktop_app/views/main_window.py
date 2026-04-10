from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableView,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from desktop_app.views.table_model import DataFrameModel


class MainWindow(QMainWindow):
    load_csv_requested = Signal()
    next_page_requested = Signal()
    prev_page_requested = Signal()
    dataset_selected = Signal(str)
    add_filter_requested = Signal()
    remove_filter_requested = Signal()
    clear_filters_requested = Signal()
    save_analysis_requested = Signal()
    load_analysis_requested = Signal()
    analysis_name_selected = Signal(str)
    save_version_requested = Signal()
    load_version_requested = Signal()
    create_branch_requested = Signal()
    compare_versions_requested = Signal()
    apply_visible_columns_requested = Signal()
    run_ols_requested = Signal()
    run_logit_requested = Signal()
    run_probit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sara Desktop")
        self.resize(1600, 920)

        self.dataset_selector = QComboBox()
        self.dataset_info_label = QLabel("Dataset: ninguno")
        self.saved_analysis_selector = QComboBox()
        self.analysis_selector = QComboBox()
        self.history_tree = QTreeWidget()
        self.filter_column_selector = QComboBox()
        self.filter_operator_selector = QComboBox()
        self.filter_input = QLineEdit()
        self.active_filters_list = QListWidget()
        self.columns_list = QListWidget()
        self.visible_columns_list = QListWidget()
        self.y_selector = QComboBox()
        self.x_selector = QListWidget()
        self.compare_version_a_selector = QComboBox()
        self.compare_version_b_selector = QComboBox()

        self.load_csv_button = QPushButton("Cargar CSV")
        self.add_filter_button = QPushButton("Agregar filtro")
        self.remove_filter_button = QPushButton("Eliminar filtro")
        self.clear_filters_button = QPushButton("Limpiar filtros")
        self.save_analysis_button = QPushButton("Guardar analisis")
        self.load_analysis_button = QPushButton("Cargar analisis")
        self.save_version_button = QPushButton("Nueva version")
        self.create_branch_button = QPushButton("Crear rama")
        self.load_version_button = QPushButton("Restaurar version")
        self.compare_versions_button = QPushButton("Comparar")
        self.apply_visible_columns_button = QPushButton("Aplicar columnas")
        self.run_ols_button = QPushButton("Run OLS")
        self.run_logit_button = QPushButton("Run Logit")
        self.run_probit_button = QPushButton("Run Probit")
        self.prev_page_button = QPushButton("Anterior")
        self.next_page_button = QPushButton("Siguiente")

        self.data_context_label = QLabel("Archivo: ninguno")
        self.page_info_label = QLabel("Mostrando filas 0-0 de 0 (Página 0)")
        self.model_status_label = QLabel("Estado del modelo: sin ejecutar")
        self.model_summary_label = QLabel("Modelo: ninguno")
        self.metrics_text = QTextEdit()
        self.interpretation_text = QTextEdit()
        self.report_text = QTextEdit()
        self.compare_results_text = QTextEdit()

        self.table_view = QTableView()
        self.compare_table_view = QTableView()
        self.coefficients_table_view = QTableView()
        self.table_model = DataFrameModel()
        self.compare_table_model = DataFrameModel()
        self.coefficients_table_model = DataFrameModel()

        self._setup_ui()
        self._connect_actions()

    def _setup_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._build_control_panel())
        splitter.addWidget(self._build_data_panel())
        splitter.addWidget(self._build_results_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([340, 720, 540])

        root_layout = QVBoxLayout()
        root_layout.addWidget(splitter)
        central_widget.setLayout(root_layout)

        self._setup_menu()

    def _build_control_panel(self) -> QWidget:
        content = QWidget(self)
        layout = QVBoxLayout()

        self.columns_list.setAlternatingRowColors(True)
        self.visible_columns_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )
        self.active_filters_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.x_selector.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.history_tree.setColumnCount(2)
        self.history_tree.setHeaderLabels(["Rama / Version", "Fecha"])
        self.history_tree.setRootIsDecorated(True)
        self.history_tree.setAlternatingRowColors(True)
        self.filter_input.setPlaceholderText("Valor del filtro")
        self.filter_operator_selector.addItems(["=", "!=", ">", ">=", "<", "<=", "LIKE"])
        self.dataset_info_label.setWordWrap(True)

        dataset_group = QGroupBox("Dataset")
        dataset_layout = QVBoxLayout()
        dataset_layout.addWidget(self.load_csv_button)
        dataset_layout.addWidget(self.dataset_selector)
        dataset_layout.addWidget(self.dataset_info_label)
        dataset_group.setLayout(dataset_layout)

        filter_group = QGroupBox("Filtros")
        filter_layout = QVBoxLayout()
        filter_form = QFormLayout()
        filter_form.addRow("Columna", self.filter_column_selector)
        filter_form.addRow("Operador", self.filter_operator_selector)
        filter_form.addRow("Valor", self.filter_input)
        filter_buttons = QHBoxLayout()
        filter_buttons.addWidget(self.add_filter_button)
        filter_buttons.addWidget(self.remove_filter_button)
        filter_layout.addLayout(filter_form)
        filter_layout.addLayout(filter_buttons)
        filter_layout.addWidget(self.clear_filters_button)
        filter_layout.addWidget(QLabel("Filtros activos"))
        filter_layout.addWidget(self.active_filters_list)
        filter_group.setLayout(filter_layout)

        variables_group = QGroupBox("Variables")
        variables_layout = QVBoxLayout()
        variables_layout.addWidget(QLabel("Variable dependiente (Y)"))
        variables_layout.addWidget(self.y_selector)
        variables_layout.addWidget(QLabel("Variables independientes (X)"))
        variables_layout.addWidget(self.x_selector)
        variables_layout.addWidget(QLabel("Columnas visibles"))
        variables_layout.addWidget(self.visible_columns_list)
        variables_layout.addWidget(self.apply_visible_columns_button)
        variables_layout.addWidget(QLabel("Metadata de columnas"))
        variables_layout.addWidget(self.columns_list)
        variables_group.setLayout(variables_layout)

        model_group = QGroupBox("Modelos")
        model_layout = QVBoxLayout()
        model_layout.addWidget(self.run_ols_button)
        model_layout.addWidget(self.run_logit_button)
        model_layout.addWidget(self.run_probit_button)
        model_layout.addWidget(self.model_status_label)
        model_group.setLayout(model_layout)

        session_group = QGroupBox("Sesiones e Historial")
        session_layout = QVBoxLayout()
        session_layout.addWidget(QLabel("Sesiones guardadas"))
        session_layout.addWidget(self.saved_analysis_selector)
        session_buttons = QHBoxLayout()
        session_buttons.addWidget(self.save_analysis_button)
        session_buttons.addWidget(self.load_analysis_button)
        session_layout.addLayout(session_buttons)
        session_layout.addWidget(QLabel("Análisis versionado"))
        session_layout.addWidget(self.analysis_selector)
        session_layout.addWidget(self.history_tree)
        history_buttons = QHBoxLayout()
        history_buttons.addWidget(self.save_version_button)
        history_buttons.addWidget(self.create_branch_button)
        session_layout.addLayout(history_buttons)
        session_layout.addWidget(self.load_version_button)
        session_group.setLayout(session_layout)

        layout.addWidget(dataset_group)
        layout.addWidget(filter_group)
        layout.addWidget(variables_group)
        layout.addWidget(model_group)
        layout.addWidget(session_group)
        layout.addStretch()
        content.setLayout(layout)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _build_data_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout()
        table_header_layout = QHBoxLayout()
        pagination_layout = QHBoxLayout()

        self.data_context_label.setWordWrap(True)

        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        table_header_layout.addWidget(self.data_context_label)
        table_header_layout.addStretch()

        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()

        layout.addLayout(table_header_layout)
        layout.addLayout(pagination_layout)
        layout.addWidget(self.table_view)
        panel.setLayout(layout)
        return panel

    def _build_results_panel(self) -> QWidget:
        content = QWidget(self)
        layout = QVBoxLayout()

        self.metrics_text.setReadOnly(True)
        self.interpretation_text.setReadOnly(True)
        self.report_text.setReadOnly(True)
        self.compare_results_text.setReadOnly(True)

        self.coefficients_table_view.setModel(self.coefficients_table_model)
        self.compare_table_view.setModel(self.compare_table_model)
        self.coefficients_table_view.setAlternatingRowColors(True)
        self.compare_table_view.setAlternatingRowColors(True)
        self.coefficients_table_view.horizontalHeader().setStretchLastSection(True)
        self.compare_table_view.horizontalHeader().setStretchLastSection(True)

        summary_group = QGroupBox("Resultado del Modelo")
        summary_layout = QVBoxLayout()
        self.model_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.model_summary_label)
        summary_group.setLayout(summary_layout)

        metrics_group = QGroupBox("Métricas")
        metrics_layout = QVBoxLayout()
        metrics_layout.addWidget(self.metrics_text)
        metrics_group.setLayout(metrics_layout)

        coefficients_group = QGroupBox("Coeficientes")
        coefficients_layout = QVBoxLayout()
        coefficients_layout.addWidget(self.coefficients_table_view)
        coefficients_group.setLayout(coefficients_layout)

        interpretation_group = QGroupBox("Interpretación Automática")
        interpretation_layout = QVBoxLayout()
        interpretation_layout.addWidget(self.interpretation_text)
        interpretation_group.setLayout(interpretation_layout)

        report_group = QGroupBox("Reporte Completo")
        report_layout = QVBoxLayout()
        report_layout.addWidget(self.report_text)
        report_group.setLayout(report_layout)

        compare_group = QGroupBox("Comparar")
        compare_layout = QVBoxLayout()
        compare_layout.addWidget(QLabel("Versión A"))
        compare_layout.addWidget(self.compare_version_a_selector)
        compare_layout.addWidget(QLabel("Versión B"))
        compare_layout.addWidget(self.compare_version_b_selector)
        compare_layout.addWidget(self.compare_versions_button)
        compare_layout.addWidget(self.compare_results_text)
        compare_layout.addWidget(self.compare_table_view)
        compare_group.setLayout(compare_layout)

        layout.addWidget(summary_group)
        layout.addWidget(metrics_group)
        layout.addWidget(coefficients_group)
        layout.addWidget(interpretation_group)
        layout.addWidget(report_group)
        layout.addWidget(compare_group)
        content.setLayout(layout)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        return scroll

    def _setup_menu(self) -> None:
        file_menu = self.menuBar().addMenu("Archivo")
        load_action = QAction("Cargar CSV", self)
        load_action.triggered.connect(self.load_csv_requested.emit)
        file_menu.addAction(load_action)

    def _connect_actions(self) -> None:
        self.load_csv_button.clicked.connect(self.load_csv_requested.emit)
        self.next_page_button.clicked.connect(self.next_page_requested.emit)
        self.prev_page_button.clicked.connect(self.prev_page_requested.emit)
        self.dataset_selector.currentTextChanged.connect(self.dataset_selected.emit)
        self.add_filter_button.clicked.connect(self.add_filter_requested.emit)
        self.remove_filter_button.clicked.connect(self.remove_filter_requested.emit)
        self.clear_filters_button.clicked.connect(self.clear_filters_requested.emit)
        self.save_analysis_button.clicked.connect(self.save_analysis_requested.emit)
        self.load_analysis_button.clicked.connect(self.load_analysis_requested.emit)
        self.analysis_selector.currentTextChanged.connect(self.analysis_name_selected.emit)
        self.save_version_button.clicked.connect(self.save_version_requested.emit)
        self.create_branch_button.clicked.connect(self.create_branch_requested.emit)
        self.load_version_button.clicked.connect(self.load_version_requested.emit)
        self.compare_versions_button.clicked.connect(self.compare_versions_requested.emit)
        self.apply_visible_columns_button.clicked.connect(
            self.apply_visible_columns_requested.emit
        )
        self.run_ols_button.clicked.connect(self.run_ols_requested.emit)
        self.run_logit_button.clicked.connect(self.run_logit_requested.emit)
        self.run_probit_button.clicked.connect(self.run_probit_requested.emit)

    def set_empty_state(self) -> None:
        self.dataset_info_label.setText("Dataset: ninguno")
        self.data_context_label.setText("Archivo: ninguno")
        self.set_table_data(None, offset=0)
        self.columns_list.clear()
        self.dataset_selector.blockSignals(True)
        self.dataset_selector.setCurrentIndex(-1)
        self.dataset_selector.blockSignals(False)
        self.y_selector.clear()
        self.x_selector.clear()
        self.visible_columns_list.clear()
        self.active_filters_list.clear()
        self.saved_analysis_selector.clear()
        self.analysis_selector.clear()
        self.history_tree.clear()
        self.filter_column_selector.clear()
        self.filter_input.clear()
        self.clear_model_results()
        self.compare_results_text.clear()
        self.compare_table_model.set_dataframe(None)
        self.set_dataset_window(0, 0, 0, 0)
        self.set_pagination_enabled(has_previous=False, has_next=False)
        self.set_model_status("Estado del modelo: sin ejecutar")

    def clear_model_results(self) -> None:
        self.model_summary_label.setText("Modelo: ninguno")
        self.metrics_text.clear()
        self.interpretation_text.clear()
        self.report_text.clear()
        self.coefficients_table_model.set_dataframe(None)

    def set_file_info(self, text: str) -> None:
        self.data_context_label.setText(text)

    def show_dataset_info(
        self,
        *,
        dataset_name: str,
        file_name: str,
        total_rows: int,
        total_columns: int,
        filters_count: int,
        order_text: str,
    ) -> None:
        self.dataset_info_label.setText(
            f"Dataset activo: {dataset_name}\n"
            f"Archivo: {file_name}\n"
            f"Filas: {total_rows:,}\n"
            f"Columnas: {total_columns:,}\n"
            f"Filtros activos: {filters_count}\n"
            f"Orden: {order_text}"
        )

    def show_table_context(self, text: str) -> None:
        self.data_context_label.setText(text)

    def set_table_data(self, dataframe, offset: int = 0) -> None:
        self.table_model.set_dataframe(dataframe, offset=offset)
        self.table_view.resizeColumnsToContents()

    def show_table(self, dataframe, offset: int = 0) -> None:
        self.set_table_data(dataframe, offset=offset)

    def set_columns_metadata(self, columns_metadata: list[tuple[str, str]]) -> None:
        self.columns_list.clear()
        for column, dtype in columns_metadata:
            self.columns_list.addItem(QListWidgetItem(f"{column} ({dtype})"))

    def add_dataset_option(self, table_name: str) -> None:
        if table_name and self.dataset_selector.findText(table_name) == -1:
            self.dataset_selector.addItem(table_name)

    def set_analysis_options(self, analyses: list[dict]) -> None:
        current_data = self.saved_analysis_selector.currentData()
        self.saved_analysis_selector.blockSignals(True)
        self.saved_analysis_selector.clear()
        for analysis in analyses:
            label = f"{analysis['name']} [{analysis['dataset']}]"
            self.saved_analysis_selector.addItem(label, analysis["id"])
        if current_data is not None:
            index = self.saved_analysis_selector.findData(current_data)
            if index >= 0:
                self.saved_analysis_selector.setCurrentIndex(index)
        self.saved_analysis_selector.blockSignals(False)

    def set_analysis_name_options(self, names: list[str]) -> None:
        current_text = self.analysis_selector.currentText()
        self.analysis_selector.blockSignals(True)
        self.analysis_selector.clear()
        for name in names:
            self.analysis_selector.addItem(name, name)
        if current_text:
            index = self.analysis_selector.findText(current_text)
            if index >= 0:
                self.analysis_selector.setCurrentIndex(index)
        self.analysis_selector.blockSignals(False)

    def set_version_options(self, versions: list[dict]) -> None:
        current_version_id = self.get_selected_version_id()
        self.history_tree.blockSignals(True)
        self.history_tree.clear()

        branch_items: dict[str, QTreeWidgetItem] = {}
        for version in sorted(
            versions,
            key=lambda item: (str(item.get("branch") or "main"), -int(item["version"])),
        ):
            branch_name = str(version.get("branch") or "main")
            branch_item = branch_items.get(branch_name)
            if branch_item is None:
                branch_item = QTreeWidgetItem([branch_name, ""])
                branch_item.setData(0, Qt.ItemDataRole.UserRole, None)
                self.history_tree.addTopLevelItem(branch_item)
                branch_items[branch_name] = branch_item

            created_at = version["created_at"]
            timestamp = (
                created_at.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(created_at, "strftime")
                else str(created_at)
            )
            version_label = f"v{version['version']}"
            if version.get("parent_version"):
                version_label += f" <- {version['parent_version']}"
            item = QTreeWidgetItem([version_label, timestamp])
            item.setData(0, Qt.ItemDataRole.UserRole, int(version["id"]))
            item.setToolTip(
                0,
                f"{version['analysis_name']} | rama={branch_name} | dataset={version['dataset']}",
            )
            branch_item.addChild(item)

        self.history_tree.expandAll()
        if current_version_id is not None:
            self._select_history_item(current_version_id)
        self.history_tree.blockSignals(False)

    def set_compare_version_options(self, versions: list[dict]) -> None:
        current_a = self.compare_version_a_selector.currentData()
        current_b = self.compare_version_b_selector.currentData()
        for selector, current in (
            (self.compare_version_a_selector, current_a),
            (self.compare_version_b_selector, current_b),
        ):
            selector.blockSignals(True)
            selector.clear()
            for version in versions:
                branch_name = version.get("branch") or "main"
                selector.addItem(
                    f"{version['analysis_name']} [{branch_name}] v{version['version']}",
                    version["id"],
                )
            if current is not None:
                index = selector.findData(current)
                if index >= 0:
                    selector.setCurrentIndex(index)
            selector.blockSignals(False)

    def set_selected_dataset(self, table_name: str) -> None:
        index = self.dataset_selector.findText(table_name)
        if index >= 0 and self.dataset_selector.currentIndex() != index:
            self.dataset_selector.blockSignals(True)
            self.dataset_selector.setCurrentIndex(index)
            self.dataset_selector.blockSignals(False)

    def set_variable_options(self, columns: list[str]) -> None:
        current_y = self.y_selector.currentText()
        selected_x = set(self.get_selected_x())
        selected_visible = set(self.get_selected_visible_columns())

        self.y_selector.blockSignals(True)
        self.y_selector.clear()
        self.y_selector.addItems(columns)
        if current_y:
            index = self.y_selector.findText(current_y)
            if index >= 0:
                self.y_selector.setCurrentIndex(index)
        self.y_selector.blockSignals(False)

        self.x_selector.clear()
        self.visible_columns_list.clear()
        self.filter_column_selector.clear()
        self.filter_column_selector.addItems(columns)
        for column in columns:
            x_item = QListWidgetItem(column)
            x_item.setSelected(column in selected_x)
            self.x_selector.addItem(x_item)

            visible_item = QListWidgetItem(column)
            visible_item.setSelected(column in selected_visible if selected_visible else True)
            self.visible_columns_list.addItem(visible_item)

    def get_selected_y(self) -> str:
        return self.y_selector.currentText().strip()

    def get_selected_x(self) -> list[str]:
        return [item.text() for item in self.x_selector.selectedItems()]

    def get_filter_text(self) -> str:
        return self.filter_input.text().strip()

    def get_selected_filter_column(self) -> str:
        return self.filter_column_selector.currentText().strip()

    def get_selected_filter_operator(self) -> str:
        return self.filter_operator_selector.currentText().strip()

    def get_selected_visible_columns(self) -> list[str]:
        return [item.text() for item in self.visible_columns_list.selectedItems()]

    def set_selected_visible_columns(self, columns: list[str]) -> None:
        selected = set(columns)
        for index in range(self.visible_columns_list.count()):
            item = self.visible_columns_list.item(index)
            item.setSelected(item.text() in selected)

    def set_active_filters(self, filters: list[str]) -> None:
        self.active_filters_list.clear()
        for filter_text in filters:
            self.active_filters_list.addItem(QListWidgetItem(filter_text))

    def get_selected_filter_index(self) -> int:
        row = self.active_filters_list.currentRow()
        return row if row >= 0 else -1

    def get_selected_analysis_id(self) -> int | None:
        analysis_id = self.saved_analysis_selector.currentData()
        return None if analysis_id is None else int(analysis_id)

    def get_selected_analysis_name(self) -> str:
        return self.analysis_selector.currentText().strip()

    def get_selected_version_id(self) -> int | None:
        current_item = self.history_tree.currentItem()
        if current_item is None:
            return None
        version_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        return None if version_id is None else int(version_id)

    def set_selected_version(self, version_id: int) -> None:
        self._select_history_item(version_id)

    def get_compare_version_ids(self) -> tuple[int | None, int | None]:
        a_id = self.compare_version_a_selector.currentData()
        b_id = self.compare_version_b_selector.currentData()
        return (
            None if a_id is None else int(a_id),
            None if b_id is None else int(b_id),
        )

    def set_selected_y(self, column: str) -> None:
        index = self.y_selector.findText(column)
        if index >= 0:
            self.y_selector.setCurrentIndex(index)

    def set_selected_x(self, columns: list[str]) -> None:
        selected = set(columns)
        for index in range(self.x_selector.count()):
            item = self.x_selector.item(index)
            item.setSelected(item.text() in selected)

    def set_results_text(self, text: str) -> None:
        self.report_text.setPlainText(text)

    def show_model_summary(self, model_name: str, formula: str, observations: int, status: str) -> None:
        self.model_summary_label.setText(
            f"Tipo de modelo: {model_name}\n"
            f"Fórmula: {formula}\n"
            f"Observaciones: {observations:,}\n"
            f"Estado: {status}"
        )

    def show_metrics(self, metrics: dict) -> None:
        if not metrics:
            self.metrics_text.clear()
            return
        lines = []
        for label, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"{label}: {value:.4f}")
            else:
                lines.append(f"{label}: {value}")
        self.metrics_text.setPlainText("\n".join(lines))

    def show_coefficients(self, dataframe: pd.DataFrame | None) -> None:
        self.coefficients_table_model.set_dataframe(dataframe)
        self.coefficients_table_view.resizeColumnsToContents()

    def show_interpretation(self, text: str) -> None:
        self.interpretation_text.setPlainText(text)

    def show_report(self, text: str) -> None:
        self.report_text.setPlainText(text)

    def set_compare_results(self, summary_text: str, dataframe) -> None:
        self.compare_results_text.setPlainText(summary_text)
        self.compare_table_model.set_dataframe(dataframe)
        self.compare_table_view.resizeColumnsToContents()

    def set_model_status(self, text: str) -> None:
        self.model_status_label.setText(text)

    def set_dataset_window(
        self,
        start_row: int,
        end_row: int,
        total_rows: int,
        page_number: int,
    ) -> None:
        self.page_info_label.setText(
            f"Mostrando filas {start_row:,}-{end_row:,} de {total_rows:,} | Página {page_number}"
        )

    def set_pagination_enabled(self, has_previous: bool, has_next: bool) -> None:
        self.prev_page_button.setEnabled(has_previous)
        self.next_page_button.setEnabled(has_next)

    def _select_history_item(self, version_id: int) -> None:
        for branch_index in range(self.history_tree.topLevelItemCount()):
            branch_item = self.history_tree.topLevelItem(branch_index)
            for child_index in range(branch_item.childCount()):
                child_item = branch_item.child(child_index)
                if child_item.data(0, Qt.ItemDataRole.UserRole) == version_id:
                    self.history_tree.setCurrentItem(child_item)
                    return
