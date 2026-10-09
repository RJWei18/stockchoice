"""Performance evaluation metrics for backtesting."""
from typing import List, Dict, Any, Optional
import numpy as np


def calculate_metrics(
    initial_capital: float,
    equity_series: List[Dict[str, Any]],
    trades: List[Dict[str, Any]],
    total_fees: float,
    days_count: int,
) -> Dict[str, Any]:
    """Calculate comprehensive performance metrics from equity curve and trades."""
    if not equity_series:
        return {
            "initial_capital": initial_capital,
            "final_equity": initial_capital,
            "total_return_pct": 0.0,
            "cagr_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "benchmark_return_pct": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "total_fees": 0.0,
        }

    final_equity = equity_series[-1]["portfolio_value"]
    total_return_pct = round(((final_equity - initial_capital) / initial_capital) * 100.0, 2)

    # CAGR (Compound Annual Growth Rate)
    years = max(days_count / 365.25, 0.05)
    if final_equity > 0 and initial_capital > 0:
        cagr_pct = round((((final_equity / initial_capital) ** (1.0 / years)) - 1.0) * 100.0, 2)
    else:
        cagr_pct = -100.0

    # Max Drawdown (MDD)
    peak = initial_capital
    max_dd_pct = 0.0
    for pt in equity_series:
        val = pt["portfolio_value"]
        if val > peak:
            peak = val
        if peak > 0:
            dd = ((peak - val) / peak) * 100.0
            if dd > max_dd_pct:
                max_dd_pct = dd
    max_drawdown_pct = round(max_dd_pct, 2)

    # Benchmark return (Buy & Hold)
    benchmark_final = equity_series[-1].get("benchmark_value", initial_capital)
    benchmark_return_pct = round(((benchmark_final - initial_capital) / initial_capital) * 100.0, 2)

    # Trades analytics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losing_trades = sum(1 for t in trades if t.get("pnl", 0) <= 0)
    win_rate_pct = round((winning_trades / total_trades * 100.0), 1) if total_trades > 0 else 0.0

    total_gross_gain = sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0)
    total_gross_loss = abs(sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) < 0))

    if total_gross_loss > 0:
        profit_factor = round(total_gross_gain / total_gross_loss, 2)
    elif total_gross_gain > 0:
        profit_factor = 99.9
    else:
        profit_factor = 0.0

    return {
        "initial_capital": round(initial_capital, 2),
        "final_equity": round(final_equity, 2),
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "benchmark_return_pct": benchmark_return_pct,
        "alpha_pct": round(total_return_pct - benchmark_return_pct, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "total_fees": round(total_fees, 2),
    }
