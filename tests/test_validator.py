from __future__ import annotations

import unittest

import duckdb
import pandas as pd

from core.dataset import Dataset
from core.exceptions import ValidationError
from core.validator import (
    validate_columns_exist,
    validate_no_nulls,
    validate_numeric_columns,
)


class ValidatorTestCase(unittest.TestCase):
    def setUp(self):
        connection = duckdb.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE sample (
                y DOUBLE,
                x1 DOUBLE,
                x2 INTEGER,
                name VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO sample VALUES
            (1.0, 10.0, 0, 'a'),
            (2.0, 11.0, 1, 'b'),
            (3.0, 12.0, 0, 'c')
            """
        )
        self.dataset = Dataset(connection=connection, base_table="sample")

    def test_validate_columns_exist_ok(self):
        validate_columns_exist(self.dataset, ["y", "x1"])

    def test_validate_columns_exist_raises_for_missing(self):
        with self.assertRaises(ValidationError):
            validate_columns_exist(self.dataset, ["missing"])

    def test_validate_numeric_columns_raises_for_text(self):
        with self.assertRaises(ValidationError):
            validate_numeric_columns(self.dataset, ["name"])

    def test_validate_no_nulls_raises_for_null_values(self):
        frame = pd.DataFrame({"y": [1.0, None], "x1": [2.0, 3.0]})
        with self.assertRaises(ValidationError):
            validate_no_nulls(frame, ["y", "x1"])


if __name__ == "__main__":
    unittest.main()
