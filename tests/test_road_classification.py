"""Regression tests for the finalized legacy missing-road class boundaries."""

import unittest

from _pkg import import_plugin

_rc = import_plugin("core.road_classification")
refined_classify_value = _rc.refined_classify_value
classify_coverage_ratio = _rc.classify_coverage_ratio


class LegacyClassificationTests(unittest.TestCase):
    def test_fully_covered_tolerance(self):
        self.assertEqual(refined_classify_value(0.0), "missing_a")
        self.assertEqual(refined_classify_value(0.01), "missing_a")

    def test_mostly_covered_is_strictly_below_quarter(self):
        self.assertEqual(refined_classify_value(0.010001), "missing_b")
        self.assertEqual(refined_classify_value(0.249999), "missing_b")

    def test_exact_quarter_remains_unclassified(self):
        self.assertIsNone(refined_classify_value(0.25))
        report = classify_coverage_ratio(0.25)
        self.assertIsNone(report["Missing_Class"])

    def test_remaining_ratio_classes(self):
        self.assertEqual(refined_classify_value(0.250001), "missing_4")
        self.assertEqual(refined_classify_value(0.50), "missing_4")
        self.assertEqual(refined_classify_value(0.500001), "missing_3")
        self.assertEqual(refined_classify_value(0.75), "missing_3")
        self.assertEqual(refined_classify_value(0.750001), "missing_2")
        self.assertEqual(refined_classify_value(0.999999), "missing_2")
        self.assertEqual(refined_classify_value(1.0), "missing_1")

    def test_invalid_ratios_are_rejected(self):
        for value in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    refined_classify_value(value)


if __name__ == "__main__":
    unittest.main()
