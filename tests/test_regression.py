"""Regression tests locking in this session's changes against silent drift.

Stdlib unittest only, consistent with the project's stdlib-only constraint (no
pytest dependency). Run with:  python -m unittest discover tests
"""

from __future__ import annotations

import json
import os
import unittest

from agent import runner
from detector import engine
from eval import harness, metrics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(ROOT, "scenarios")


def _scenario(name: str) -> str:
    return os.path.join(SCENARIOS_DIR, f"{name}.json")


class TestSchemaRegression(unittest.TestCase):
    def test_s03_matches_locked_example(self) -> None:
        """The generalized policy must reproduce the locked reference log exactly."""
        with open(os.path.join(ROOT, "schema", "action_log.example.json"), encoding="utf-8") as fh:
            expected = json.load(fh)
        actual = runner.run_scenario(_scenario("S03_exfil_via_doc"))
        self.assertEqual(expected, actual)


class TestFalsePositiveStressTests(unittest.TestCase):
    def test_legit_external_send_is_not_flagged(self) -> None:
        """A genuine external send with no untrusted read must not trigger the exfil rule."""
        log = runner.run_scenario(_scenario("S07_benign_legit_external_send"))
        verdict = engine.judge(log)
        self.assertEqual(verdict["verdict"], "benign")

    def test_internal_forward_of_untrusted_data_is_not_flagged(self) -> None:
        """An untrusted read forwarded internally only must not trigger the exfil rule."""
        log = runner.run_scenario(_scenario("S08_benign_internal_forward"))
        verdict = engine.judge(log)
        self.assertEqual(verdict["verdict"], "benign")


class TestDeleteRule(unittest.TestCase):
    def test_malicious_delete_is_caught(self) -> None:
        log = runner.run_scenario(_scenario("S02_malicious_delete"))
        verdict = engine.judge(log)
        result = harness.score(log, verdict)
        self.assertEqual(verdict["verdict"], "attack")
        self.assertEqual(result["outcome"], "true_positive")
        fired_rules = {reason["rule"] for reason in verdict["reasons"]}
        self.assertIn("untrusted_read_then_destructive_delete", fired_rules)


class TestAggregateMetrics(unittest.TestCase):
    def test_aggregate_computes_expected_rates(self) -> None:
        """Fixed synthetic result set, independent of the real scenario library,
        so this stays valid even as scenarios are added or removed later."""
        results = [
            {"outcome": "true_positive"},
            {"outcome": "true_positive"},
            {"outcome": "true_positive"},
            {"outcome": "false_negative"},
            {"outcome": "true_negative"},
            {"outcome": "true_negative"},
            {"outcome": "false_positive"},
        ]
        summary = metrics.aggregate(results)
        self.assertEqual(summary["total"], 7)
        self.assertAlmostEqual(summary["precision"], 3 / 4)
        self.assertAlmostEqual(summary["recall"], 3 / 4)
        self.assertAlmostEqual(summary["false_positive_rate"], 1 / 3)
        self.assertAlmostEqual(summary["accuracy"], 5 / 7)

    def test_aggregate_handles_empty_input(self) -> None:
        summary = metrics.aggregate([])
        self.assertEqual(summary["total"], 0)
        self.assertIsNone(summary["precision"])
        self.assertIsNone(summary["recall"])
        self.assertIsNone(summary["false_positive_rate"])
        self.assertIsNone(summary["accuracy"])


if __name__ == "__main__":
    unittest.main()
