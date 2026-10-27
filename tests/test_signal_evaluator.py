"""Unit tests for Signal Outcome Evaluation Engine."""
import unittest
from src.backtest.signal_evaluator import evaluate_signal_status, EvaluationResult


class TestSignalEvaluator(unittest.TestCase):
    def setUp(self):
        self.base_date = "2026-01-01"
        self.entry_price = 100.0

    def _generate_bars(self, count, close_val, high_offset=1.0, low_offset=1.0, start_day=2):
        bars = []
        for i in range(count):
            day = start_day + i
            day_str = f"2026-01-{day:02d}" if day <= 31 else f"2026-02-{(day-31):02d}"
            bars.append({
                "date": day_str,
                "open": close_val,
                "high": close_val + high_offset,
                "low": close_val - low_offset,
                "close": close_val,
            })
        return bars

    def test_bullish_take_profit_win(self):
        signal = {
            "signal_type": "BULLISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 110.0,
            "stop_loss_price": 95.0,
        }
        bars = [
            {"date": "2026-01-02", "open": 100.0, "high": 102.0, "low": 98.0, "close": 101.0},
            {"date": "2026-01-03", "open": 101.0, "high": 111.5, "low": 99.0, "close": 110.5},
        ]
        res = evaluate_signal_status(signal, bars)
        self.assertEqual(res.status, "WIN")
        self.assertEqual(res.reason, "TAKE_PROFIT")
        self.assertEqual(res.resolved_date, "2026-01-03")
        self.assertEqual(res.resolved_price, 110.0)
        self.assertEqual(res.holding_bars, 2)
        self.assertEqual(res.return_pct, 10.0)

    def test_bullish_stop_loss_loss(self):
        signal = {
            "signal_type": "BULLISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 110.0,
            "stop_loss_price": 95.0,
        }
        bars = [
            {"date": "2026-01-02", "open": 100.0, "high": 101.0, "low": 98.0, "close": 99.0},
            {"date": "2026-01-03", "open": 98.0, "high": 99.0, "low": 94.0, "close": 94.5},
        ]
        res = evaluate_signal_status(signal, bars)
        self.assertEqual(res.status, "LOSS")
        self.assertEqual(res.reason, "STOP_LOSS")
        self.assertEqual(res.resolved_date, "2026-01-03")
        self.assertEqual(res.resolved_price, 95.0)
        self.assertEqual(res.holding_bars, 2)
        self.assertEqual(res.return_pct, -5.0)

    def test_bullish_intraday_conflict_conservative_loss(self):
        signal = {
            "signal_type": "BULLISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 110.0,
            "stop_loss_price": 95.0,
        }
        # Extreme volatility day: hits both 112 (TP) and 93 (SL)
        bars = [
            {"date": "2026-01-02", "open": 100.0, "high": 112.0, "low": 93.0, "close": 105.0},
        ]
        res = evaluate_signal_status(signal, bars)
        self.assertEqual(res.status, "LOSS")
        self.assertEqual(res.reason, "INTRADAY_LOSS_CONSERVATIVE")
        self.assertEqual(res.resolved_date, "2026-01-02")
        self.assertEqual(res.resolved_price, 95.0)

    def test_bullish_timeout_loss(self):
        signal = {
            "signal_type": "BULLISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 110.0,
            "stop_loss_price": 95.0,
        }
        # 63 bars oscillating around 100 without hitting 110 or 95
        bars = self._generate_bars(63, 100.0, high_offset=2.0, low_offset=2.0)
        res = evaluate_signal_status(signal, bars, timeout_bars=63)
        self.assertEqual(res.status, "LOSS")
        self.assertEqual(res.reason, "TIMEOUT_EXPIRED")
        self.assertEqual(res.holding_bars, 63)

    def test_bullish_pending(self):
        signal = {
            "signal_type": "BULLISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 110.0,
            "stop_loss_price": 95.0,
        }
        # Only 20 bars passed, neither hit
        bars = self._generate_bars(20, 100.0, high_offset=2.0, low_offset=2.0)
        res = evaluate_signal_status(signal, bars, timeout_bars=63)
        self.assertEqual(res.status, "PENDING")
        self.assertEqual(res.reason, "PENDING_ACTIVE")
        self.assertEqual(res.holding_bars, 20)

    def test_bearish_take_profit_win(self):
        signal = {
            "signal_type": "BEARISH",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
            "take_profit_price": 90.0,
            "stop_loss_price": 105.0,
        }
        bars = [
            {"date": "2026-01-02", "open": 99.0, "high": 101.0, "low": 89.5, "close": 90.5},
        ]
        res = evaluate_signal_status(signal, bars)
        self.assertEqual(res.status, "WIN")
        self.assertEqual(res.reason, "TAKE_PROFIT")
        self.assertEqual(res.return_pct, 10.0)

    def test_neutral_range_bound_win(self):
        signal = {
            "signal_type": "NEUTRAL",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
        }
        # 63 bars fluctuating within 95 ~ 105 (+/- 5% < 10%)
        bars = self._generate_bars(63, 100.0, high_offset=4.0, low_offset=4.0)
        res = evaluate_signal_status(signal, bars, timeout_bars=63, range_bound_threshold_pct=10.0)
        self.assertEqual(res.status, "WIN")
        self.assertEqual(res.reason, "RANGE_BOUND_WIN")
        self.assertEqual(res.holding_bars, 63)

    def test_neutral_threshold_breached_loss(self):
        signal = {
            "signal_type": "NEUTRAL",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
        }
        # Bar 5 jumps to 111 (+11% >= +10%)
        bars = self._generate_bars(4, 100.0, high_offset=2.0, low_offset=2.0)
        bars.append({"date": "2026-01-06", "open": 105.0, "high": 111.0, "low": 104.0, "close": 110.5})
        res = evaluate_signal_status(signal, bars, timeout_bars=63, range_bound_threshold_pct=10.0)
        self.assertEqual(res.status, "LOSS")
        self.assertEqual(res.reason, "THRESHOLD_BREACHED")
        self.assertEqual(res.resolved_date, "2026-01-06")
        self.assertEqual(res.holding_bars, 5)

    def test_neutral_pending(self):
        signal = {
            "signal_type": "NEUTRAL",
            "entry_price": 100.0,
            "entry_date": "2026-01-01",
        }
        # Only 10 bars passed, all within range
        bars = self._generate_bars(10, 100.0, high_offset=2.0, low_offset=2.0)
        res = evaluate_signal_status(signal, bars, timeout_bars=63)
        self.assertEqual(res.status, "PENDING")
        self.assertEqual(res.reason, "PENDING_ACTIVE")
        self.assertEqual(res.holding_bars, 10)


if __name__ == "__main__":
    unittest.main()
