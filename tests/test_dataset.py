from __future__ import annotations

import unittest

import duckdb

from core.dataset import Dataset
from core.exceptions import ValidationError


class DatasetTestCase(unittest.TestCase):
    def setUp(self):
        connection = duckdb.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE personas (
                edad INTEGER,
                ingreso DOUBLE,
                segmento VARCHAR
            )
            """
        )
        connection.execute(
            """
            INSERT INTO personas VALUES
            (30, 1000.0, 'a'),
            (40, 1500.0, 'b'),
            (50, 2000.0, 'a')
            """
        )
        self.dataset = Dataset(connection=connection, base_table="personas")

    def test_get_metadata_returns_expected_sections(self):
        metadata = self.dataset.get_metadata()
        self.assertEqual(metadata["columns"], ["edad", "ingreso", "segmento"])
        self.assertTrue(metadata["types"]["edad"])
        self.assertEqual(metadata["null_counts"]["ingreso"], 0)
        self.assertEqual(metadata["cardinality"]["segmento"], 2)
        self.assertAlmostEqual(metadata["stats"]["ingreso"]["mean"], 1500.0)

    def test_filter_validates_and_sanitizes(self):
        filtered = self.dataset.filter("edad >= 40")
        self.assertEqual(
            filtered.build_query(),
            'SELECT * FROM "personas" WHERE ("edad" >= 40)',
        )

    def test_filter_rejects_unsafe_sql(self):
        with self.assertRaises(ValidationError):
            self.dataset.filter("edad >= 40; DROP TABLE personas")

    def test_filter_supports_aliases(self):
        filtered = self.dataset.with_aliases({"age": "edad"}).filter("age >= 40")
        self.assertEqual(filtered.query()["edad"].tolist(), [40, 50])


if __name__ == "__main__":
    unittest.main()
