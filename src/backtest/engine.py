"""Core rule-based backtesting engine."""
from typing import Dict, Any, List, Optional
import os
import pandas as pd
from datetime import datetime, timedelta

from src.backtest.metrics import calculate_metrics


class BacktestEngine:
    """Simulates trading strategies across historical bar sequences."""

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001425,
        tax_rate: float = 0.003,
        min_commission: float = 20.0,
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.tax_rate = tax_rate
        self.min_commission = min_commission

    def run_dip_momentum_strategy(
        self,
        df: pd.DataFrame,
        buy_dip_pct: float = 10.0,
        take_profit_pct: float = 10.0,
        stop_loss_pct: Optional[float] = None,
        is_tw: bool = True,
    ) -> Dict[str, Any]:
        """Execute a rule-based backtest.
        
        Rules:
        - Entry: Buy when price declines >= buy_dip_pct from the highest price observed since last exit.
        - Exit (TP): Sell when price >= avg_cost * (1 + take_profit_pct / 100).
        - Exit (SL): Sell when stop_loss_pct is set and price <= avg_cost * (1 - stop_loss_pct / 100).
        """
        if df.empty or len(df) < 5:
            return {
                "metrics": calculate_metrics(self.initial_capital, [], [], 0.0, 0),
                "trades": [],
                "equity_curve": [],
            }

        # Normalize dataframe
        df = df.copy().sort_values("date").reset_index(drop=True)
        if "close" not in df.columns:
            raise ValueError("Dataframe must contain 'close' column")

        cash = float(self.initial_capital)
        shares = 0
        avg_cost = 0.0
        total_fees = 0.0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []

        first_close = float(df.iloc[0]["close"])
        benchmark_shares = int(self.initial_capital / first_close) if first_close > 0 else 0
        benchmark_cash_rem = self.initial_capital - (benchmark_shares * first_close)

        recent_peak = float(df.iloc[0]["close"])
        entry_date = None
        entry_price = 0.0

        tax_rate = self.tax_rate if is_tw else 0.0
        comm_rate = self.commission_rate if is_tw else 0.0005
        min_comm = self.min_commission if is_tw else 1.0

        for idx, row in df.iterrows():
            date_str = str(row["date"])
            close = float(row["close"])
            high = float(row.get("high", close))
            low = float(row.get("low", close))

            # Update peak while not holding full position
            if shares == 0:
                if high > recent_peak:
                    recent_peak = high
            else:
                if high > recent_peak:
                    recent_peak = high

            # 1. Check Exit Conditions if holding
            if shares > 0:
                tp_target = avg_cost * (1.0 + (take_profit_pct / 100.0))
                sl_target = avg_cost * (1.0 - (stop_loss_pct / 100.0)) if stop_loss_pct and stop_loss_pct > 0 else None

                exit_triggered = False
                exit_price = close
                exit_reason = ""

                # Check take profit against high or close
                if high >= tp_target:
                    exit_triggered = True
                    exit_price = tp_target if low <= tp_target <= high else close
                    exit_reason = "TAKE_PROFIT"
                # Check stop loss against low or close
                elif sl_target is not None and low <= sl_target:
                    exit_triggered = True
                    exit_price = sl_target if low <= sl_target <= high else close
                    exit_reason = "STOP_LOSS"

                if exit_triggered:
                    gross_proceeds = shares * exit_price
                    fee = max(gross_proceeds * comm_rate, min_comm)
                    tax = gross_proceeds * tax_rate
                    total_fees += (fee + tax)
                    net_proceeds = gross_proceeds - fee - tax
                    cash += net_proceeds

                    pnl = net_proceeds - (shares * avg_cost)
                    pnl_pct = round((pnl / (shares * avg_cost)) * 100.0, 2) if avg_cost > 0 else 0.0

                    trades.append({
                        "entry_date": entry_date,
                        "entry_price": round(entry_price, 2),
                        "exit_date": date_str,
                        "exit_price": round(exit_price, 2),
                        "shares": shares,
                        "pnl": round(pnl, 2),
                        "return_pct": pnl_pct,
                        "reason": exit_reason,
                    })

                    shares = 0
                    avg_cost = 0.0
                    entry_date = None
                    entry_price = 0.0
                    recent_peak = close  # Reset peak tracking

            # 2. Check Entry Conditions if in cash
            if shares == 0 and cash >= (close * 10):
                dip_threshold = recent_peak * (1.0 - (buy_dip_pct / 100.0))
                if low <= dip_threshold:
                    buy_price = dip_threshold if low <= dip_threshold <= high else close
                    # Allocate full available cash minus commission
                    affordable_shares = int(cash / (buy_price * (1.0 + comm_rate)))
                    if affordable_shares > 0:
                        gross_cost = affordable_shares * buy_price
                        fee = max(gross_cost * comm_rate, min_comm)
                        total_fees += fee
                        total_outlay = gross_cost + fee

                        cash -= total_outlay
                        shares = affordable_shares
                        avg_cost = buy_price
                        entry_date = date_str
                        entry_price = buy_price
                        recent_peak = buy_price

            # Record daily equity
            portfolio_val = cash + (shares * close)
            bench_val = (benchmark_shares * close) + benchmark_cash_rem
            equity_curve.append({
                "date": date_str,
                "portfolio_value": round(portfolio_val, 2),
                "benchmark_value": round(bench_val, 2),
                "cash": round(cash, 2),
                "shares": shares,
                "close": close,
            })

        # Calculate time span in days
        try:
            d_start = datetime.strptime(str(df.iloc[0]["date"])[:10], "%Y-%m-%d")
            d_end = datetime.strptime(str(df.iloc[-1]["date"])[:10], "%Y-%m-%d")
            days_count = max((d_end - d_start).days, len(df))
        except Exception:
            days_count = len(df)

        metrics = calculate_metrics(
            initial_capital=self.initial_capital,
            equity_series=equity_curve,
            trades=trades,
            total_fees=total_fees,
            days_count=days_count,
        )

        return {
            "metrics": metrics,
            "trades": trades,
            "equity_curve": equity_curve,
        }
