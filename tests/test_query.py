from __future__ import annotations

import unittest

import duckdb

from core.dataset import Dataset
from core.exceptions import ValidationError
from core.query import filter_data, order_by


class QueryTestCase(unittest.TestCase):
    def setUp(self):
        connection = duckdb.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE sample (
                edad INTEGER,
                ingreso DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO sample VALUES
            (30, 1000.0),
            (40, 1500.0),
            (50, 2000.0)
            """
        )
        self.dataset = Dataset(connection=connection, base_table="sample")

    def test_filter_data_applies_alias_validation(self):
        scoped = filter_data(self.dataset, "age >= 40", aliases={"age": "edad"})
        self.assertEqual(scoped.get_shape()[0], 2)

    def test_order_by_rejects_missing_column(self):
        with self.assertRaises(ValidationError):
            order_by(self.dataset, "missing")


if __name__ == "__main__":
    unittest.main()
