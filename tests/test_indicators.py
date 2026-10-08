"""Unit tests for Technical Analysis indicators and strategies."""

import unittest
import numpy as np
import pandas as pd
from src.ta_engine.indicators import TechnicalIndicators
from src.scanner.strategy import BreakoutResistanceStrategy, GoldenCrossQuarterMaStrategy, Scanner


class TestTechnicalIndicators(unittest.TestCase):
    """Test suite for technical indicators calculation."""

    def setUp(self):
        """Prepare synthetic price dataset."""
        dates = pd.date_range("2024-01-01", periods=80, freq="D").strftime("%Y-%m-%d").tolist()
        closes = [100.0 + i * 0.5 for i in range(79)]
        highs = [c + 0.5 for c in closes]
        lows = [c - 0.5 for c in closes]
        opens = [c - 0.1 for c in closes]
        volumes = [1000.0] * 79

        # 80th day: Strong breakout above the 20-day high (highest previous was ~140, breakout at 160)
        closes.append(160.0)
        highs.append(162.0)
        lows.append(158.0)
        opens.append(150.0)
        volumes.append(3000.0)  # 3x volume surge

        self.df = pd.DataFrame(
            {
                "date": dates,
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            }
        )

    def test_moving_averages(self):
        """Verify SMA computation accuracy."""
        res = TechnicalIndicators.add_moving_averages(self.df, [5, 20])
        self.assertIn("ma_5", res.columns)
        self.assertIn("ma_20", res.columns)

        # Check last ma_5 value
        expected_ma5 = np.mean(self.df["close"].iloc[-5:])
        self.assertAlmostEqual(res["ma_5"].iloc[-1], expected_ma5, places=4)

    def test_donchian_channels(self):
        """Verify dynamic support and resistance calculation."""
        res = TechnicalIndicators.add_donchian_channels(self.df, window=20)
        self.assertIn("resistance_20", res.columns)
        self.assertIn("support_20", res.columns)

        # resistance_20 for last row should be max of high from previous 20 rows
        expected_res = self.df["high"].iloc[-21:-1].max()
        self.assertAlmostEqual(res["resistance_20"].iloc[-1], expected_res, places=4)

    def test_volume_metrics(self):
        """Verify volume ratio surge detection."""
        res = TechnicalIndicators.add_volume_metrics(self.df, window=5)
        self.assertIn("vol_ratio", res.columns)
        # Last volume is 3000 vs 1000 average -> ratio 3.0
        self.assertAlmostEqual(res["vol_ratio"].iloc[-1], 3.0, places=2)

    def test_breakout_strategy_signal(self):
        """Verify BreakoutResistanceStrategy triggers when price breaks resistance."""
        strat = BreakoutResistanceStrategy(window=20, min_vol_ratio=1.5)
        sig = strat.evaluate(self.df, "AAPL")
        self.assertIsNotNone(sig)
        self.assertEqual(sig.ticker, "AAPL")
        self.assertIn("突破", sig.strategy_name)

    def test_scanner_runner(self):
        """Verify Scanner evaluates multiple strategies cleanly."""
        scanner = Scanner()
        signals = scanner.scan_ticker(self.df, "NVDA")
        self.assertIsInstance(signals, list)
        self.assertGreater(len(signals), 0)


if __name__ == "__main__":
    unittest.main()
