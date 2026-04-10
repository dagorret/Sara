from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.core.dataset import Dataset


@dataclass(slots=True)
class DatasetModel:
    dataset: Dataset

    @property
    def path(self) -> str:
        return self.dataset.path

    @property
    def table_name(self) -> str:
        return self.dataset.table_name

    def get_shape(self) -> tuple[int, int]:
        return self.dataset.get_shape()

    def get_columns(self) -> list[str]:
        return self.dataset.get_columns()

    def get_base_columns(self) -> list[str]:
        return self.dataset.get_base_columns()

    def get_preview(self, n: int = 10) -> pd.DataFrame:
        return self.dataset.get_preview(limit=n)

    def get_page(self, limit: int, offset: int) -> pd.DataFrame:
        return self.dataset.get_page(limit=limit, offset=offset)

    def get_dtypes(self) -> dict[str, str]:
        return self.dataset.get_dtypes()

    def get_columns_metadata(self) -> list[tuple[str, str]]:
        dtypes = self.get_dtypes()
        return [(column, dtypes[column]) for column in self.get_columns()]

    def filter(self, condition: str) -> DatasetModel:
        return DatasetModel(dataset=self.dataset.filter(condition))

    def order_by(self, column: str, ascending: bool = True) -> DatasetModel:
        return DatasetModel(dataset=self.dataset.order_by(column, ascending=ascending))

    def select(self, columns: list[str] | None) -> DatasetModel:
        return DatasetModel(dataset=self.dataset.select(columns))

    def reset_query(self) -> DatasetModel:
        return DatasetModel(dataset=self.dataset.reset_query())

    def get_state(self) -> dict:
        return self.dataset.get_state()
