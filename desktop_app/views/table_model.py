from __future__ import annotations

import math

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


class DataFrameModel(QAbstractTableModel):
    def __init__(
        self,
        dataframe: pd.DataFrame | None = None,
        offset: int = 0,
        highlight_pvalues: bool = False,
    ) -> None:
        super().__init__()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._offset = max(offset, 0)
        self._highlight_pvalues = bool(highlight_pvalues)

    def set_dataframe(self, dataframe: pd.DataFrame | None, offset: int = 0) -> None:
        self.beginResetModel()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._offset = max(offset, 0)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._dataframe.index)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._dataframe.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        value = self._dataframe.iat[index.row(), index.column()]
        if role == Qt.ItemDataRole.BackgroundRole and self._highlight_pvalues:
            color = self._coefficient_background(index.row())
            if color is not None:
                return color
            return None
        if role == Qt.ItemDataRole.ForegroundRole and self._highlight_pvalues:
            color = self._coefficient_color(index.row())
            if color is not None:
                return color
            return None

        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if pd.isna(value):
            return ""
        if isinstance(value, float) and math.isfinite(value):
            return f"{value:g}"
        return str(value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            return str(self._dataframe.columns[section])

        return str(self._offset + section)

    def _coefficient_color(self, row: int):
        if "p-value" not in self._dataframe.columns:
            return None
        try:
            pvalue = float(self._dataframe.iloc[row]["p-value"])
        except Exception:
            return None
        if pvalue < 0.05:
            return QColor("#1f5132")
        return QColor("#5f6368")

    def _coefficient_background(self, row: int):
        if "p-value" not in self._dataframe.columns:
            return None
        try:
            pvalue = float(self._dataframe.iloc[row]["p-value"])
        except Exception:
            return None
        if pvalue < 0.05:
            return QColor("#e6f4ea")
        return QColor("#f1f3f4")
