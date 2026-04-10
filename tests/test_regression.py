from __future__ import annotations

import unittest

import pandas as pd

from core.exceptions import ValidationError
from core.model_result import ModelResult
from core.regression import run_ols, run_pipeline


class RegressionTestCase(unittest.TestCase):
    def test_run_ols_returns_model_result(self):
        frame = pd.DataFrame(
            {
                "y": [1.0, 2.0, 3.0, 4.0],
                "x1": [1.0, 2.0, 3.0, 4.0],
                "x2": [2.0, 1.0, 0.0, -1.0],
            }
        )
        result, warnings_list = run_ols(frame, "y", ["x1", "x2"])
        self.assertIsInstance(result, ModelResult)
        self.assertIsInstance(result.summary, str)
        self.assertEqual(warnings_list, [])

    def test_run_ols_raises_on_nulls(self):
        frame = pd.DataFrame({"y": [1.0, None], "x1": [2.0, 3.0]})
        with self.assertRaises(ValidationError):
            run_ols(frame, "y", ["x1"])

    def test_run_pipeline_returns_evaluation_and_report(self):
        frame = pd.DataFrame(
            {
                "y": [1.0, 2.0, 3.0, 4.0, 5.0],
                "x1": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        output = run_pipeline(frame, "y", ["x1"], "ols")
        self.assertIn("result", output)
        self.assertIn("evaluation", output)
        self.assertIn("report", output)


if __name__ == "__main__":
    unittest.main()
