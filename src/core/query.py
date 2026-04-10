from __future__ import annotations

from .dataset import Dataset


def select_columns(dataset: Dataset, columns: list[str] | tuple[str, ...]):
    return dataset.select(columns)


def filter_data(
    dataset: Dataset,
    conditions: str | list[str] | tuple[str, ...],
    columns: list[str] | tuple[str, ...] | None = None,
):
    scoped_dataset = dataset.select(columns) if columns is not None else dataset
    if isinstance(conditions, str):
        return scoped_dataset.filter(conditions)

    result = scoped_dataset
    for condition in conditions:
        result = result.filter(condition)
    return result


def order_by(
    dataset: Dataset,
    column: str,
    ascending: bool = True,
    columns: list[str] | tuple[str, ...] | None = None,
):
    scoped_dataset = dataset.select(columns) if columns is not None else dataset
    return scoped_dataset.order_by(column, ascending=ascending)


def limit_offset(
    dataset: Dataset,
    limit: int,
    offset: int,
    columns: list[str] | tuple[str, ...] | None = None,
    conditions: str | list[str] | tuple[str, ...] | None = None,
    order_column: str | None = None,
    ascending: bool = True,
):
    scoped_dataset = dataset.select(columns) if columns is not None else dataset
    if conditions:
        scoped_dataset = filter_data(scoped_dataset, conditions)
    if order_column:
        scoped_dataset = scoped_dataset.order_by(order_column, ascending=ascending)
    return scoped_dataset.get_page(limit=limit, offset=offset)
