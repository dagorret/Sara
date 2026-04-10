from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTableView,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from desktop_app.views.log_handler import QtLogHandler
from desktop_app.views.table_model import DataFrameModel


class MainWindow(QMainWindow):
    load_csv_requested = Signal()
    save_analysis_requested = Signal()
    load_analysis_requested = Signal()
    exit_requested = Signal()
    show_metadata_requested = Signal()
    clear_filters_requested = Signal()
    next_page_requested = Signal()
    prev_page_requested = Signal()
    dataset_selected = Signal(str)
    add_filter_requested = Signal()
    remove_filter_requested = Signal()
    run_ols_requested = Signal()
    run_logit_requested = Signal()
    run_probit_requested = Signal()
    show_simple_report_requested = Signal()
    show_technical_report_requested = Signal()
    show_interpretative_report_requested = Signal()
    export_txt_requested = Signal()
    export_csv_requested = Signal()
    copy_report_requested = Signal()
    copy_full_report_requested = Signal()
    export_full_report_requested = Signal()
    show_logs_requested = Signal()
    show_settings_requested = Signal()
    variable_selection_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SARA Analytics Desktop")
        self.resize(1760, 980)

        self.dataset_selector = QComboBox()
        self.dataset_rows_label = QLabel("Filas: 0")
        self.dataset_columns_label = QLabel("Columnas: 0")
        self.dataset_filters_label = QLabel("Filtros activos: 0")

        self.filter_column_selector = QComboBox()
        self.filter_operator_selector = QComboBox()
        self.filter_input = QLineEdit()
        self.active_filters_list = QListWidget()

        self.y_selector = QComboBox()
        self.x_selector = QListWidget()

        self.add_filter_button = QPushButton("Agregar filtro")
        self.remove_filter_button = QPushButton("Quitar seleccionado")
        self.clear_filters_button = QPushButton("Limpiar filtros")
        self.run_ols_button = QPushButton("Run OLS")
        self.run_logit_button = QPushButton("Run Logit")
        self.run_probit_button = QPushButton("Run Probit")
        self.prev_page_button = QPushButton("Anterior")
        self.next_page_button = QPushButton("Siguiente")

        self.table_info_label = QLabel("Mostrando filas 0-0 de 0 | Filtros: 0 | Orden: sin orden")
        self.page_info_label = QLabel("Página 0 / 0")
        self.dataset_badge_label = QLabel("Sin dataset activo")
        self.feedback_label = QLabel("Listo")
        self.analysis_state_label = QLabel(
            "Dataset: ninguno | Filtros: sin filtros | Modelo: sin ejecutar | Variables: -"
        )

        self.table_view = QTableView()
        self.table_model = DataFrameModel()
        self.coefficients_table_view = QTableView()
        self.coefficients_table_model = DataFrameModel(highlight_pvalues=True)

        self.results_tabs = QTabWidget()
        self.model_summary_text = QTextBrowser()
        self.metrics_text = QTextBrowser()
        self.interpretation_text = QTextBrowser()
        self.report_text = QTextBrowser()
        self.full_report_text = QTextBrowser()
        self.latex_text = QPlainTextEdit()
        self.report_mode_label = QLabel("Reporte principal: markdown")
        self.copy_report_button = QPushButton("Copiar reporte")
        self.export_coefficients_button = QPushButton("Exportar coeficientes CSV")
        self.copy_full_report_button = QPushButton("Copiar todo")
        self.export_full_report_button = QPushButton("Exportar TXT")
        self.logs_text = QPlainTextEdit()

        self.log_dock = QDockWidget("Logs", self)
        self.log_handler = QtLogHandler(self.append_log_line)

        self._setup_ui()
        self._connect_actions()
        self._refresh_run_buttons()

    def _setup_ui(self) -> None:
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Listo")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        root_splitter.addWidget(self._build_control_panel())
        root_splitter.addWidget(self._build_workspace_panel())
        root_splitter.setSizes([380, 1280])
        root_splitter.setCollapsible(0, False)
        root_splitter.setCollapsible(1, False)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(root_splitter)
        central_widget.setLayout(layout)

        self._setup_results_tabs()
        self._setup_logs_dock()
        self._setup_menu()
        self._apply_styles()

    def _build_control_panel(self) -> QWidget:
        content = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        self.filter_operator_selector.addItems(["=", "!=", ">", ">=", "<", "<=", "LIKE"])
        self.filter_input.setPlaceholderText("Valor del filtro")
        self.active_filters_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.x_selector.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)

        dataset_group = QGroupBox("Dataset")
        dataset_layout = QVBoxLayout()
        dataset_layout.addWidget(self.dataset_selector)
        dataset_layout.addWidget(self.dataset_rows_label)
        dataset_layout.addWidget(self.dataset_columns_label)
        dataset_layout.addWidget(self.dataset_filters_label)
        dataset_group.setLayout(dataset_layout)

        filters_group = QGroupBox("Filtros")
        filters_layout = QVBoxLayout()
        filter_form = QFormLayout()
        filter_form.addRow("Columna", self.filter_column_selector)
        filter_form.addRow("Operador", self.filter_operator_selector)
        filter_form.addRow("Valor", self.filter_input)
        filters_layout.addLayout(filter_form)
        filters_layout.addWidget(self.add_filter_button)
        filters_layout.addWidget(self.remove_filter_button)
        filters_layout.addWidget(self.clear_filters_button)
        filters_layout.addWidget(QLabel("Filtros activos"))
        filters_layout.addWidget(self.active_filters_list)
        filters_group.setLayout(filters_layout)

        variables_group = QGroupBox("Variables")
        variables_layout = QVBoxLayout()
        variables_layout.addWidget(QLabel("Variable dependiente (Y)"))
        variables_layout.addWidget(self.y_selector)
        variables_layout.addWidget(QLabel("Variables explicativas (X)"))
        variables_layout.addWidget(self.x_selector)
        variables_group.setLayout(variables_layout)

        models_group = QGroupBox("Modelos")
        models_layout = QVBoxLayout()
        models_layout.addWidget(self.run_ols_button)
        models_layout.addWidget(self.run_logit_button)
        models_layout.addWidget(self.run_probit_button)
        models_layout.addWidget(self.feedback_label)
        models_group.setLayout(models_layout)

        layout.addWidget(dataset_group)
        layout.addWidget(filters_group)
        layout.addWidget(variables_group)
        layout.addWidget(models_group)
        layout.addStretch()
        content.setLayout(layout)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    def _build_workspace_panel(self) -> QWidget:
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.addWidget(self._build_data_panel())
        splitter.addWidget(self._build_results_panel())
        splitter.setSizes([520, 420])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        return splitter

    def _build_data_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self.dataset_badge_label)
        header_layout.addStretch()

        info_layout = QHBoxLayout()
        self.table_info_label.setWordWrap(True)
        info_layout.addWidget(self.table_info_label, 1)

        pager_layout = QHBoxLayout()
        pager_layout.addWidget(self.prev_page_button)
        pager_layout.addWidget(self.next_page_button)
        pager_layout.addWidget(self.page_info_label)
        pager_layout.addStretch()

        self.table_view.setModel(self.table_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(False)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)
        layout.addLayout(pager_layout)
        layout.addWidget(self.table_view)
        panel.setLayout(layout)
        return panel

    def _build_results_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.analysis_state_label.setWordWrap(True)
        self.analysis_state_label.setObjectName("analysisStateLabel")
        layout.addWidget(self.analysis_state_label)
        layout.addWidget(self.results_tabs)
        panel.setLayout(layout)
        return panel

    def _setup_results_tabs(self) -> None:
        self.model_summary_text.setReadOnly(True)
        self.metrics_text.setReadOnly(True)
        self.interpretation_text.setReadOnly(True)
        self.report_text.setReadOnly(True)
        self.full_report_text.setReadOnly(True)
        self.latex_text.setReadOnly(True)
        self.logs_text.setReadOnly(True)

        self.coefficients_table_view.setModel(self.coefficients_table_model)
        self.coefficients_table_view.setAlternatingRowColors(True)
        self.coefficients_table_view.horizontalHeader().setStretchLastSection(True)

        self.results_tabs.addTab(self._wrap_text_tab(self.model_summary_text), "Modelo")
        self.results_tabs.addTab(self._wrap_text_tab(self.metrics_text), "Métricas")
        self.results_tabs.addTab(self._wrap_table_tab(self.coefficients_table_view), "Coeficientes")
        self.results_tabs.addTab(self._wrap_text_tab(self.interpretation_text), "Interpretación")

        report_tab = QWidget(self)
        report_layout = QVBoxLayout()
        report_layout.setContentsMargins(8, 8, 8, 8)
        report_actions_layout = QHBoxLayout()
        report_actions_layout.addWidget(self.report_mode_label)
        report_actions_layout.addStretch()
        report_actions_layout.addWidget(self.copy_report_button)
        report_actions_layout.addWidget(self.export_coefficients_button)
        report_layout.addLayout(report_actions_layout)
        report_layout.addWidget(self.report_text)
        report_tab.setLayout(report_layout)
        self.results_tabs.addTab(report_tab, "Reporte")
        full_report_tab = QWidget(self)
        full_report_layout = QVBoxLayout()
        full_report_layout.setContentsMargins(8, 8, 8, 8)
        full_report_actions_layout = QHBoxLayout()
        full_report_actions_layout.addWidget(QLabel("Documento completo"))
        full_report_actions_layout.addStretch()
        full_report_actions_layout.addWidget(self.copy_full_report_button)
        full_report_actions_layout.addWidget(self.export_full_report_button)
        full_report_layout.addLayout(full_report_actions_layout)
        full_report_layout.addWidget(self.full_report_text)
        full_report_tab.setLayout(full_report_layout)
        self.results_tabs.addTab(full_report_tab, "Reporte completo")

        self.results_tabs.addTab(self._wrap_plain_text_tab(self.latex_text), "LaTeX")

    def _setup_logs_dock(self) -> None:
        self.log_dock.setWidget(self.logs_text)
        self.log_dock.setFloating(False)
        self.log_dock.hide()
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Archivo")
        load_action = QAction("Cargar dataset", self)
        load_action.triggered.connect(self.load_csv_requested.emit)
        file_menu.addAction(load_action)

        save_analysis_action = QAction("Guardar análisis", self)
        save_analysis_action.triggered.connect(self.save_analysis_requested.emit)
        file_menu.addAction(save_analysis_action)

        load_analysis_action = QAction("Cargar análisis", self)
        load_analysis_action.triggered.connect(self.load_analysis_requested.emit)
        file_menu.addAction(load_analysis_action)

        file_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        file_menu.addAction(exit_action)

        data_menu = menu_bar.addMenu("Datos")
        metadata_action = QAction("Ver metadata", self)
        metadata_action.triggered.connect(self.show_metadata_requested.emit)
        data_menu.addAction(metadata_action)

        reset_filters_action = QAction("Resetear filtros", self)
        reset_filters_action.triggered.connect(self.clear_filters_requested.emit)
        data_menu.addAction(reset_filters_action)

        models_menu = menu_bar.addMenu("Modelos")
        run_ols_action = QAction("Ejecutar OLS", self)
        run_ols_action.triggered.connect(self.run_ols_requested.emit)
        models_menu.addAction(run_ols_action)

        run_logit_action = QAction("Ejecutar Logit", self)
        run_logit_action.triggered.connect(self.run_logit_requested.emit)
        models_menu.addAction(run_logit_action)

        run_probit_action = QAction("Ejecutar Probit", self)
        run_probit_action.triggered.connect(self.run_probit_requested.emit)
        models_menu.addAction(run_probit_action)

        reports_menu = menu_bar.addMenu("Reportes")
        simple_report_action = QAction("Ver reporte simple", self)
        simple_report_action.triggered.connect(self.show_simple_report_requested.emit)
        reports_menu.addAction(simple_report_action)

        technical_report_action = QAction("Ver reporte técnico", self)
        technical_report_action.triggered.connect(self.show_technical_report_requested.emit)
        reports_menu.addAction(technical_report_action)

        interpretative_report_action = QAction("Ver reporte interpretativo", self)
        interpretative_report_action.triggered.connect(self.show_interpretative_report_requested.emit)
        reports_menu.addAction(interpretative_report_action)

        reports_menu.addSeparator()

        export_txt_action = QAction("Exportar TXT", self)
        export_txt_action.triggered.connect(self.export_txt_requested.emit)
        reports_menu.addAction(export_txt_action)

        export_csv_action = QAction("Exportar CSV", self)
        export_csv_action.triggered.connect(self.export_csv_requested.emit)
        reports_menu.addAction(export_csv_action)

        tools_menu = menu_bar.addMenu("Herramientas")
        logs_action = QAction("Ver logs", self)
        logs_action.triggered.connect(self.show_logs_requested.emit)
        tools_menu.addAction(logs_action)

        settings_action = QAction("Configuración", self)
        settings_action.triggered.connect(self.show_settings_requested.emit)
        tools_menu.addAction(settings_action)

    def _connect_actions(self) -> None:
        self.dataset_selector.currentTextChanged.connect(self.dataset_selected.emit)
        self.add_filter_button.clicked.connect(self.add_filter_requested.emit)
        self.remove_filter_button.clicked.connect(self.remove_filter_requested.emit)
        self.clear_filters_button.clicked.connect(self.clear_filters_requested.emit)
        self.run_ols_button.clicked.connect(self.run_ols_requested.emit)
        self.run_logit_button.clicked.connect(self.run_logit_requested.emit)
        self.run_probit_button.clicked.connect(self.run_probit_requested.emit)
        self.prev_page_button.clicked.connect(self.prev_page_requested.emit)
        self.next_page_button.clicked.connect(self.next_page_requested.emit)
        self.copy_report_button.clicked.connect(self.copy_report_requested.emit)
        self.export_coefficients_button.clicked.connect(self.export_csv_requested.emit)
        self.copy_full_report_button.clicked.connect(self.copy_full_report_requested.emit)
        self.export_full_report_button.clicked.connect(self.export_full_report_requested.emit)
        self.y_selector.currentTextChanged.connect(self._handle_variable_selection_change)
        self.x_selector.itemSelectionChanged.connect(self._handle_variable_selection_change)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #fbfbfa;
                color: #222222;
                font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                margin-top: 12px;
                padding: 14px 10px 10px 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #3c4858;
            }
            QPushButton {
                background: #ffffff;
                color: #2b3a42;
                border: 1px solid #cfd7df;
                border-radius: 5px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f4f7fa;
            }
            QPushButton:disabled {
                background: #f2f2f2;
                color: #a2a8ad;
                border-color: #e1e1e1;
            }
            QComboBox, QLineEdit, QListWidget, QTableView, QTextBrowser, QPlainTextEdit, QTabWidget::pane {
                background: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
            }
            QTableView {
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
                color: #222222;
                gridline-color: #dddddd;
                selection-background-color: #cce5ff;
                selection-color: #222222;
            }
            QTabBar::tab {
                background: #f1f3f5;
                color: #44515c;
                padding: 8px 14px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin-right: 2px;
                border: 1px solid #d9d9d9;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1f3b59;
                border-bottom-color: #ffffff;
            }
            QLabel {
                color: #2f3b45;
            }
            QLabel#analysisStateLabel {
                background: #f7f7f7;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 10px 12px;
                color: #374151;
                font-weight: 600;
            }
            QScrollArea {
                background: #f7f7f7;
                border: none;
            }
            QTextBrowser, QPlainTextEdit {
                padding: 14px;
                line-height: 1.45em;
            }
            """
        )
        self._apply_document_styles()

    def _wrap_text_tab(self, widget: QTextBrowser) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        container.setLayout(layout)
        return container

    def _wrap_plain_text_tab(self, widget: QPlainTextEdit) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        container.setLayout(layout)
        return container

    def _wrap_table_tab(self, widget: QTableView) -> QWidget:
        container = QWidget(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(widget)
        container.setLayout(layout)
        return container

    def set_empty_state(self) -> None:
        self.dataset_rows_label.setText("Filas: 0")
        self.dataset_columns_label.setText("Columnas: 0")
        self.dataset_filters_label.setText("Filtros activos: 0")
        self.dataset_badge_label.setText("Sin dataset activo")
        self.table_info_label.setText("Mostrando filas 0-0 de 0 | Filtros: 0 | Orden: sin orden")
        self.page_info_label.setText("Página 0 / 0")
        self.dataset_selector.blockSignals(True)
        self.dataset_selector.setCurrentIndex(-1)
        self.dataset_selector.blockSignals(False)
        self.filter_column_selector.clear()
        self.filter_input.clear()
        self.active_filters_list.clear()
        self.y_selector.clear()
        self.x_selector.clear()
        self.show_table(None)
        self.clear_model_results()
        self.show_analysis_state(
            dataset_name=None,
            filters=None,
            model_name=None,
            y_column=None,
            x_columns=None,
        )
        self.set_has_dataset(False)
        self.show_feedback("Listo")

    def show_feedback(self, text: str, *, error: bool = False) -> None:
        self.feedback_label.setText(text)
        self.feedback_label.setStyleSheet(
            "color: #8f2d2d; font-weight: 600;" if error else "color: #204e4a; font-weight: 600;"
        )
        self.statusBar().showMessage(text)

    def show_dataset_info(
        self,
        *,
        dataset_name: str,
        total_rows: int,
        total_columns: int,
        filters_count: int,
    ) -> None:
        self.dataset_badge_label.setText(f"Dataset activo: {dataset_name}")
        self.dataset_rows_label.setText(f"Filas: {total_rows:,}")
        self.dataset_columns_label.setText(f"Columnas: {total_columns:,}")
        self.dataset_filters_label.setText(f"Filtros activos: {filters_count}")

    def show_table_context(
        self,
        *,
        start_row: int,
        end_row: int,
        total_rows: int,
        filters_count: int,
        order_text: str,
        page_number: int,
        total_pages: int,
    ) -> None:
        self.table_info_label.setText(
            f"Mostrando filas {start_row:,}-{end_row:,} de {total_rows:,} | "
            f"Filtros: {filters_count} | Orden: {order_text}"
        )
        self.page_info_label.setText(f"Página {page_number} / {total_pages}")

    def show_table(self, dataframe: pd.DataFrame | None, offset: int = 0) -> None:
        self.table_model.set_dataframe(dataframe, offset=offset)
        self.table_view.resizeColumnsToContents()

    def add_dataset_option(self, table_name: str) -> None:
        if table_name and self.dataset_selector.findText(table_name) == -1:
            self.dataset_selector.addItem(table_name)

    def set_selected_dataset(self, table_name: str) -> None:
        index = self.dataset_selector.findText(table_name)
        if index >= 0 and self.dataset_selector.currentIndex() != index:
            self.dataset_selector.blockSignals(True)
            self.dataset_selector.setCurrentIndex(index)
            self.dataset_selector.blockSignals(False)

    def set_variable_options(self, columns: list[str]) -> None:
        current_y = self.get_selected_y()
        selected_x = set(self.get_selected_x())

        self.y_selector.blockSignals(True)
        self.y_selector.clear()
        self.y_selector.addItems(columns)
        if current_y:
            index = self.y_selector.findText(current_y)
            if index >= 0:
                self.y_selector.setCurrentIndex(index)
        self.y_selector.blockSignals(False)

        self.x_selector.clear()
        self.filter_column_selector.clear()
        self.filter_column_selector.addItems(columns)
        for column in columns:
            item = QListWidgetItem(column)
            item.setSelected(column in selected_x)
            self.x_selector.addItem(item)
        self._refresh_run_buttons()

    def set_selected_y(self, column: str) -> None:
        index = self.y_selector.findText(column)
        if index >= 0:
            self.y_selector.setCurrentIndex(index)
        self._refresh_run_buttons()

    def set_selected_x(self, columns: list[str]) -> None:
        selected = set(columns)
        for index in range(self.x_selector.count()):
            item = self.x_selector.item(index)
            item.setSelected(item.text() in selected)
        self._refresh_run_buttons()

    def set_active_filters(self, filters: list[str]) -> None:
        self.active_filters_list.clear()
        for filter_text in filters:
            self.active_filters_list.addItem(filter_text)

    def get_selected_y(self) -> str:
        return self.y_selector.currentText().strip()

    def get_selected_x(self) -> list[str]:
        return [item.text() for item in self.x_selector.selectedItems()]

    def get_selected_filter_column(self) -> str:
        return self.filter_column_selector.currentText().strip()

    def get_selected_filter_operator(self) -> str:
        return self.filter_operator_selector.currentText().strip()

    def get_filter_text(self) -> str:
        return self.filter_input.text().strip()

    def clear_filter_input(self) -> None:
        self.filter_input.clear()

    def get_selected_filter_index(self) -> int:
        return self.active_filters_list.currentRow()

    def set_pagination_enabled(self, *, has_previous: bool, has_next: bool) -> None:
        self.prev_page_button.setEnabled(has_previous)
        self.next_page_button.setEnabled(has_next)

    def show_model_summary(self, result: dict[str, object]) -> None:
        lines = [
            f"### {result.get('model_name', 'Modelo')}",
            "",
            f"- **Fórmula:** `{result.get('formula', '-')}`",
            f"- **Observaciones:** {result.get('observations', 0):,}",
            f"- **Estado:** {result.get('status', '-')}",
        ]
        warnings = result.get("warnings") or []
        if warnings:
            lines.extend(["", "**Advertencias**"])
            lines.extend(f"- {warning}" for warning in warnings)
        self.model_summary_text.setMarkdown("\n".join(lines))

    def show_metrics(self, metrics: dict[str, object]) -> None:
        if not metrics:
            self.metrics_text.clear()
            return
        lines = ["### Métricas", ""]
        for label, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"- **{label}:** {value:.4f}")
            else:
                lines.append(f"- **{label}:** {value}")
        self.metrics_text.setMarkdown("\n".join(lines))

    def show_coefficients(self, dataframe: pd.DataFrame | None) -> None:
        self.coefficients_table_model.set_dataframe(dataframe)
        self.coefficients_table_view.resizeColumnsToContents()

    def show_interpretation(self, text: str) -> None:
        self.interpretation_text.setMarkdown(text)

    def show_report(self, markdown: str, *, title: str = "Reporte principal: markdown") -> None:
        self.report_mode_label.setText(title)
        self.report_text.setMarkdown(markdown)

    def show_full_report(self, text: str) -> None:
        self.full_report_text.setMarkdown(text)

    def show_latex(self, latex: str) -> None:
        self.latex_text.setPlainText(latex)

    def show_report_empty_state(self, state: str) -> None:
        messages = {
            "no_model": (
                "### Reporte\n\n"
                "No hay resultados todavía.\n"
                "Seleccioná dataset, variables y ejecutá un modelo."
            ),
            "missing_variables": (
                "### Reporte\n\n"
                "Faltan variables para ejecutar el modelo."
            ),
            "ready": (
                "### Reporte\n\n"
                "Listo para ejecutar modelo."
            ),
        }
        self.show_report(
            messages.get(state, messages["no_model"]),
            title="Reporte principal: estado actual",
        )
        self.show_full_report(messages.get(state, messages["no_model"]))

    def clear_model_results(self) -> None:
        self.model_summary_text.setMarkdown("### Modelo\n\nNo hay resultados todavía.")
        self.metrics_text.setMarkdown("### Métricas\n\nEjecutá un modelo para ver métricas persistentes.")
        self.coefficients_table_model.set_dataframe(None)
        self.interpretation_text.setMarkdown(
            "### Interpretación\n\nLa interpretación automática aparecerá aquí."
        )
        self.show_report_empty_state("no_model")
        self.show_full_report(
            "### Reporte completo\n\nEl documento final del análisis aparecerá aquí."
        )
        self.show_latex("% La salida LaTeX aparecerá aquí.")

    def focus_results(self, tab_name: str = "Reporte") -> None:
        self.results_tabs.parentWidget().setVisible(True)
        for index in range(self.results_tabs.count()):
            if self.results_tabs.tabText(index).lower() == tab_name.lower():
                self.results_tabs.setCurrentIndex(index)
                self.results_tabs.setFocus()
                return

    def append_log_line(self, text: str) -> None:
        self.logs_text.appendPlainText(text)

    def toggle_logs_panel(self) -> None:
        self.log_dock.setVisible(not self.log_dock.isVisible())

    def get_log_handler(self) -> QtLogHandler:
        return self.log_handler

    def _apply_document_styles(self) -> None:
        document_style = """
            body {
                font-family: 'Georgia', 'Times New Roman', serif;
                color: #222222;
                line-height: 1.6;
                max-width: 920px;
                margin: 0 auto;
            }
            h1, h2, h3 {
                color: #1f3b59;
                margin-top: 1.2em;
                margin-bottom: 0.45em;
            }
            p, li {
                margin-bottom: 0.55em;
            }
            ul {
                margin-left: 1.2em;
            }
            code {
                background: #f3f4f6;
                padding: 2px 4px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }
            th, td {
                border: 1px solid #dddddd;
                padding: 6px 8px;
                text-align: left;
            }
            th {
                background: #f7f7f7;
            }
        """
        self.model_summary_text.document().setDefaultStyleSheet(document_style)
        self.metrics_text.document().setDefaultStyleSheet(document_style)
        self.interpretation_text.document().setDefaultStyleSheet(document_style)
        self.report_text.document().setDefaultStyleSheet(document_style)
        self.full_report_text.document().setDefaultStyleSheet(document_style)

    def show_analysis_state(
        self,
        *,
        dataset_name: str | None,
        filters: list[str] | None,
        model_name: str | None,
        y_column: str | None,
        x_columns: list[str] | None,
    ) -> None:
        filter_text = "sin filtros"
        if filters:
            filter_text = " | ".join(filters)
        model_text = model_name or "sin ejecutar"
        variables_text = "-"
        if y_column and x_columns:
            variables_text = f"{y_column} ~ {' + '.join(x_columns)}"
        elif y_column:
            variables_text = f"{y_column} ~ ?"
        self.analysis_state_label.setText(
            f"Dataset: {dataset_name or 'ninguno'} | "
            f"Filtros: {filter_text} | "
            f"Modelo: {model_text} | "
            f"Variables: {variables_text}"
        )

    def set_has_dataset(self, has_dataset: bool) -> None:
        self.dataset_selector.setEnabled(True)
        self.filter_column_selector.setEnabled(has_dataset)
        self.filter_operator_selector.setEnabled(has_dataset)
        self.filter_input.setEnabled(has_dataset)
        self.add_filter_button.setEnabled(has_dataset)
        self.remove_filter_button.setEnabled(has_dataset)
        self.clear_filters_button.setEnabled(has_dataset)
        self.y_selector.setEnabled(has_dataset)
        self.x_selector.setEnabled(has_dataset)
        self._refresh_run_buttons(has_dataset=has_dataset)

    def set_busy(self, busy: bool) -> None:
        self.centralWidget().setEnabled(not busy)
        self.menuBar().setEnabled(not busy)
        self.log_dock.setEnabled(not busy)
        self.statusBar().showMessage("Procesando..." if busy else self.feedback_label.text())

    def _handle_variable_selection_change(self) -> None:
        self._refresh_run_buttons()
        self.variable_selection_changed.emit()

    def _refresh_run_buttons(self, has_dataset: bool | None = None) -> None:
        dataset_ready = has_dataset if has_dataset is not None else self.y_selector.isEnabled()
        y_selected = bool(self.get_selected_y())
        x_selected = bool(self.get_selected_x())
        enabled = dataset_ready and y_selected and x_selected
        self.run_ols_button.setEnabled(enabled)
        self.run_logit_button.setEnabled(enabled)
        self.run_probit_button.setEnabled(enabled)
