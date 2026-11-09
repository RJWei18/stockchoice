"""Unit tests for Macro Fetcher and OTC Margin Maintenance Evaluator."""

import unittest
from src.data_ingestion.macro_fetcher import (
    evaluate_margin_maintenance,
    MarginGaugeResult,
)


class TestMacroFetcher(unittest.TestCase):
    """Test suite for evaluate_margin_maintenance logic."""

    def test_extreme_panic_bottom(self):
        """Test ratio below 145% (extreme panic margin call / liquidation)."""
        res = evaluate_margin_maintenance(143.5, "2026-11-05")
        self.assertEqual(res.status, "PANIC_BOTTOM")
        self.assertEqual(res.color, "emerald")
        self.assertEqual(res.score_modifier, 15)
        self.assertIn("極限警戒線", res.description)
        self.assertIn("00631L", res.strategy_tip)

    def test_moderate_panic_bottom(self):
        """Test ratio between 145% and 150%."""
        res = evaluate_margin_maintenance(148.0, "2026-11-06")
        self.assertEqual(res.status, "PANIC_BOTTOM")
        self.assertEqual(res.color, "emerald")
        self.assertEqual(res.score_modifier, 10)
        self.assertIn("落入 150% 以下", res.description)

    def test_healthy_normal_range(self):
        """Test ratio between 150% and 205%."""
        res = evaluate_margin_maintenance(165.2, "2026-11-07")
        self.assertEqual(res.status, "HEALTHY_NORMAL")
        self.assertEqual(res.color, "indigo")
        self.assertEqual(res.score_modifier, 0)
        self.assertIn("常態", res.status_label)

    def test_moderate_overheated(self):
        """Test ratio between 205% and 210%."""
        res = evaluate_margin_maintenance(207.5, "2026-11-08")
        self.assertEqual(res.status, "OVERHEATED")
        self.assertEqual(res.color, "rose")
        self.assertEqual(res.score_modifier, -15)
        self.assertIn("槓桿過熱警戒區", res.status_label)

    def test_extreme_overheated(self):
        """Test ratio above 210%."""
        res = evaluate_margin_maintenance(215.0, "2026-11-09")
        self.assertEqual(res.status, "OVERHEATED")
        self.assertEqual(res.color, "rose")
        self.assertEqual(res.score_modifier, -20)
        self.assertIn("衝破 210%", res.description)
        self.assertIn("全數停利", res.strategy_tip)

    def test_to_dict_serialization(self):
        """Verify MarginGaugeResult serialization."""
        res = evaluate_margin_maintenance(156.4, "2026-11-06")
        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["ratio"], 156.4)
        self.assertEqual(d["status"], "HEALTHY_NORMAL")


if __name__ == "__main__":
    unittest.main()
