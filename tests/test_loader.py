from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from core.dataset import Dataset
from core.exceptions import ValidationError
from core.loader import load_dataset


class LoaderTestCase(unittest.TestCase):
    def test_load_dataset_reads_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "demo.csv"
            csv_path.write_text("y,x1\n1,2\n3,4\n", encoding="utf-8")

            dataset = load_dataset(str(csv_path))

            self.assertIsInstance(dataset, Dataset)
            self.assertEqual(dataset.get_shape(), (2, 2))

    def test_load_dataset_raises_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(ValidationError):
                load_dataset(str(Path(tmp_dir) / "missing.csv"))


if __name__ == "__main__":
    unittest.main()
