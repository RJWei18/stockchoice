"""Signal Outcome Evaluation Engine (訊號勝負判定與回測生命週期機制)

Pure function evaluator for trading signal outcomes based on Take-Profit,
Stop-Loss, Intraday Conflict, Range-Bound Thresholds, and Time-Out rules.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class EvaluationResult:
    status: str  # 'WIN', 'LOSS', 'PENDING'
    reason: str  # 'TAKE_PROFIT', 'STOP_LOSS', 'TIMEOUT_EXPIRED', 'THRESHOLD_BREACHED', 'INTRADAY_LOSS_CONSERVATIVE', 'PENDING_ACTIVE'
    resolved_date: Optional[str] = None
    resolved_price: Optional[float] = None
    holding_bars: int = 0
    return_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def evaluate_signal_status(
    signal: Dict[str, Any],
    price_history: List[Dict[str, Any]],
    timeout_bars: int = 63,
    range_bound_threshold_pct: float = 10.0,
) -> EvaluationResult:
    """Evaluates the lifecycle outcome of a single trading signal against price history.

    Rules:
    Case A (BULLISH):
      - Hits take_profit before stop_loss -> WIN (TAKE_PROFIT)
      - Hits stop_loss before take_profit -> LOSS (STOP_LOSS)
      - Intraday conflict (both high >= TP and low <= SL) -> LOSS (INTRADAY_LOSS_CONSERVATIVE)
      - Neither hit after timeout_bars (default 63 bars / 90 days) -> LOSS (TIMEOUT_EXPIRED)
      - Neither hit and holding_bars < timeout_bars -> PENDING (PENDING_ACTIVE)

    Case B (BEARISH):
      - Hits lower take_profit before higher stop_loss -> WIN (TAKE_PROFIT)
      - Hits higher stop_loss before lower take_profit -> LOSS (STOP_LOSS)
      - Intraday conflict -> LOSS (INTRADAY_LOSS_CONSERVATIVE)
      - Neither hit after timeout_bars -> LOSS (TIMEOUT_EXPIRED)
      - Neither hit and holding_bars < timeout_bars -> PENDING (PENDING_ACTIVE)

    Case C (NEUTRAL):
      - Breaches +/- range_bound_threshold_pct (default 10%) -> LOSS (THRESHOLD_BREACHED)
      - Stays strictly within range for timeout_bars -> WIN (RANGE_BOUND_WIN)
      - Stays within range and holding_bars < timeout_bars -> PENDING (PENDING_ACTIVE)
    """
    signal_type = str(signal.get("signal_type", "BULLISH")).upper()
    entry_price = float(signal.get("entry_price", 0.0))
    entry_date = str(signal.get("entry_date", ""))

    if entry_price <= 0:
        return EvaluationResult(status="PENDING", reason="INVALID_ENTRY_PRICE", holding_bars=0)

    # Standardize and filter bars occurring strictly AFTER entry_date
    bars_after = []
    for b in price_history:
        b_date = str(b.get("date") or b.get("time") or "")
        if b_date > entry_date:
            open_p = float(b.get("open", b.get("close", 0.0)))
            close_p = float(b.get("close", 0.0))
            high_p = float(b.get("high", max(open_p, close_p)))
            low_p = float(b.get("low", min(open_p, close_p)))
            bars_after.append({
                "date": b_date,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p,
            })

    if not bars_after:
        return EvaluationResult(
            status="PENDING",
            reason="PENDING_ACTIVE",
            resolved_date=None,
            resolved_price=None,
            holding_bars=0,
            return_pct=0.0,
        )

    # ------------------ Case A: BULLISH (LONG) ------------------
    if signal_type == "BULLISH":
        tp_price = float(signal.get("take_profit_price") or (entry_price * 1.10))
        sl_price = float(signal.get("stop_loss_price") or (entry_price * 0.95))

        for idx, bar in enumerate(bars_after):
            holding_count = idx + 1
            hit_tp = bar["high"] >= tp_price
            hit_sl = bar["low"] <= sl_price

            # Intraday conflict: both hit on same bar -> conservative LOSS priority
            if hit_tp and hit_sl:
                ret = round(((sl_price - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="INTRADAY_LOSS_CONSERVATIVE",
                    resolved_date=bar["date"],
                    resolved_price=sl_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )
            elif hit_tp:
                ret = round(((tp_price - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="WIN",
                    reason="TAKE_PROFIT",
                    resolved_date=bar["date"],
                    resolved_price=tp_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )
            elif hit_sl:
                ret = round(((sl_price - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="STOP_LOSS",
                    resolved_date=bar["date"],
                    resolved_price=sl_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )

            # Check timeout reach within loop
            if holding_count >= timeout_bars:
                ret = round(((bar["close"] - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="TIMEOUT_EXPIRED",
                    resolved_date=bar["date"],
                    resolved_price=bar["close"],
                    holding_bars=holding_count,
                    return_pct=ret,
                )

        # Still within timeout and neither hit
        cur_ret = round(((bars_after[-1]["close"] - entry_price) / entry_price) * 100.0, 2)
        return EvaluationResult(
            status="PENDING",
            reason="PENDING_ACTIVE",
            resolved_date=None,
            resolved_price=None,
            holding_bars=len(bars_after),
            return_pct=cur_ret,
        )

    # ------------------ Case B: BEARISH (SHORT/HEDGE) ------------------
    elif signal_type == "BEARISH":
        tp_price = float(signal.get("take_profit_price") or (entry_price * 0.90))
        sl_price = float(signal.get("stop_loss_price") or (entry_price * 1.05))

        for idx, bar in enumerate(bars_after):
            holding_count = idx + 1
            hit_tp = bar["low"] <= tp_price
            hit_sl = bar["high"] >= sl_price

            if hit_tp and hit_sl:
                ret = round(((entry_price - sl_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="INTRADAY_LOSS_CONSERVATIVE",
                    resolved_date=bar["date"],
                    resolved_price=sl_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )
            elif hit_tp:
                ret = round(((entry_price - tp_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="WIN",
                    reason="TAKE_PROFIT",
                    resolved_date=bar["date"],
                    resolved_price=tp_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )
            elif hit_sl:
                ret = round(((entry_price - sl_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="STOP_LOSS",
                    resolved_date=bar["date"],
                    resolved_price=sl_price,
                    holding_bars=holding_count,
                    return_pct=ret,
                )

            if holding_count >= timeout_bars:
                ret = round(((entry_price - bar["close"]) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="TIMEOUT_EXPIRED",
                    resolved_date=bar["date"],
                    resolved_price=bar["close"],
                    holding_bars=holding_count,
                    return_pct=ret,
                )

        cur_ret = round(((entry_price - bars_after[-1]["close"]) / entry_price) * 100.0, 2)
        return EvaluationResult(
            status="PENDING",
            reason="PENDING_ACTIVE",
            resolved_date=None,
            resolved_price=None,
            holding_bars=len(bars_after),
            return_pct=cur_ret,
        )

    # ------------------ Case C: NEUTRAL (RANGE-BOUND) ------------------
    else:
        threshold_ratio = range_bound_threshold_pct / 100.0
        upper_bound = entry_price * (1.0 + threshold_ratio)
        lower_bound = entry_price * (1.0 - threshold_ratio)

        for idx, bar in enumerate(bars_after):
            holding_count = idx + 1
            if bar["high"] >= upper_bound:
                ret = round(((bar["high"] - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="THRESHOLD_BREACHED",
                    resolved_date=bar["date"],
                    resolved_price=bar["high"],
                    holding_bars=holding_count,
                    return_pct=ret,
                )
            if bar["low"] <= lower_bound:
                ret = round(((bar["low"] - entry_price) / entry_price) * 100.0, 2)
                return EvaluationResult(
                    status="LOSS",
                    reason="THRESHOLD_BREACHED",
                    resolved_date=bar["date"],
                    resolved_price=bar["low"],
                    holding_bars=holding_count,
                    return_pct=ret,
                )

            # Successfully remained within range for full timeout period
            if holding_count >= timeout_bars:
                return EvaluationResult(
                    status="WIN",
                    reason="RANGE_BOUND_WIN",
                    resolved_date=bar["date"],
                    resolved_price=bar["close"],
                    holding_bars=holding_count,
                    return_pct=0.0,
                )

        return EvaluationResult(
            status="PENDING",
            reason="PENDING_ACTIVE",
            resolved_date=None,
            resolved_price=None,
            holding_bars=len(bars_after),
            return_pct=0.0,
        )
