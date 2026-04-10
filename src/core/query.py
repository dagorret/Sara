from __future__ import annotations

import logging

from .dataset import Dataset


log = logging.getLogger(__name__)


def select_columns(dataset: Dataset, columns: list[str] | tuple[str, ...]):
    log.info("Selecting columns through query helper: %s", list(columns))
    return dataset.select(columns)


def filter_data(
    dataset: Dataset,
    conditions: str | list[str] | tuple[str, ...],
    columns: list[str] | tuple[str, ...] | None = None,
    aliases: dict[str, str] | None = None,
):
    scoped_dataset = dataset.with_aliases(aliases) if aliases else dataset
    scoped_dataset = scoped_dataset.select(columns) if columns is not None else scoped_dataset

    if isinstance(conditions, str):
        log.info("Applying single filter condition: %s", conditions)
        return scoped_dataset.filter(conditions)

    result = scoped_dataset
    for condition in conditions:
        log.info("Applying filter condition: %s", condition)
        result = result.filter(condition)
    return result


def order_by(
    dataset: Dataset,
    column: str,
    ascending: bool = True,
    columns: list[str] | tuple[str, ...] | None = None,
    aliases: dict[str, str] | None = None,
):
    scoped_dataset = dataset.with_aliases(aliases) if aliases else dataset
    scoped_dataset = scoped_dataset.select(columns) if columns is not None else scoped_dataset
    return scoped_dataset.order_by(column, ascending=ascending)


def limit_offset(
    dataset: Dataset,
    limit: int,
    offset: int,
    columns: list[str] | tuple[str, ...] | None = None,
    conditions: str | list[str] | tuple[str, ...] | None = None,
    order_column: str | None = None,
    ascending: bool = True,
    aliases: dict[str, str] | None = None,
):
    scoped_dataset = dataset.with_aliases(aliases) if aliases else dataset
    scoped_dataset = scoped_dataset.select(columns) if columns is not None else scoped_dataset
    if conditions:
        scoped_dataset = filter_data(scoped_dataset, conditions)
    if order_column:
        scoped_dataset = scoped_dataset.order_by(order_column, ascending=ascending)
    return scoped_dataset.get_page(limit=limit, offset=offset)
