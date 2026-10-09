"""Unit tests for the BacktestEngine and metrics."""
import unittest
import pandas as pd
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import calculate_metrics


class TestBacktestEngine(unittest.TestCase):

    def setUp(self):
        self.engine = BacktestEngine(initial_capital=100000.0)

    def test_empty_dataframe(self):
        res = self.engine.run_dip_momentum_strategy(pd.DataFrame())
        self.assertEqual(res["metrics"]["total_trades"], 0)
        self.assertEqual(res["metrics"]["total_return_pct"], 0.0)

    def test_single_profitable_trade(self):
        # Create a synthetic series:
        # Peak at 100 -> Dips to 89 (satisfying -10% from 100) -> Rallies to 99 (satisfying +10% from 89 -> 97.9)
        dates = [f"2026-01-0{i+1}" for i in range(7)]
        prices = [100.0, 100.0, 89.0, 92.0, 95.0, 99.0, 100.0]
        df = pd.DataFrame({
            "date": dates,
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [1000] * 7,
        })

        res = self.engine.run_dip_momentum_strategy(
            df,
            buy_dip_pct=10.0,
            take_profit_pct=10.0,
            stop_loss_pct=15.0,
            is_tw=True,
        )

        metrics = res["metrics"]
        trades = res["trades"]

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["reason"], "TAKE_PROFIT")
        self.assertGreater(trades[0]["pnl"], 0)
        self.assertGreater(metrics["final_equity"], 100000.0)
        self.assertEqual(metrics["win_rate_pct"], 100.0)
        self.assertGreater(metrics["total_fees"], 0.0)

    def test_stop_loss_trigger(self):
        # Peak at 100 -> Dips to 90 (buys) -> Falls to 75 (slips past -15% stop loss from 90 -> 76.5)
        dates = [f"2026-01-0{i+1}" for i in range(5)]
        prices = [100.0, 90.0, 88.0, 75.0, 75.0]
        df = pd.DataFrame({
            "date": dates,
            "open": prices,
            "high": prices,
            "low": prices,
            "close": prices,
            "volume": [1000] * 5,
        })

        res = self.engine.run_dip_momentum_strategy(
            df,
            buy_dip_pct=10.0,
            take_profit_pct=10.0,
            stop_loss_pct=15.0,
            is_tw=True,
        )

        trades = res["trades"]
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["reason"], "STOP_LOSS")
        self.assertLess(trades[0]["pnl"], 0)
        self.assertEqual(res["metrics"]["winning_trades"], 0)
        self.assertEqual(res["metrics"]["losing_trades"], 1)
        self.assertEqual(res["metrics"]["win_rate_pct"], 0.0)
        self.assertGreater(res["metrics"]["max_drawdown_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
