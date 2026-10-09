"""Stock Strategy Scanner.

Defines strategy interfaces and concrete rules for technical screening.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from src.ta_engine.indicators import TechnicalIndicators


@dataclass
class StrategySignal:
    """Represents a strategy match result."""

    ticker: str
    strategy_name: str
    date: str
    close_price: float
    message: str
    details: dict


class BaseStrategy(ABC):
    """Abstract base class for technical trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the strategy."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief explanation of strategy rules."""
        pass

    @abstractmethod
    def evaluate(self, df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]:
        """Evaluate stock data and return a signal if criteria are satisfied."""
        pass


class BreakoutResistanceStrategy(BaseStrategy):
    """Signals when price breaks above 20-day resistance with volume surge."""

    def __init__(self, window: int = 20, min_vol_ratio: float = 1.5):
        self.window = window
        self.min_vol_ratio = min_vol_ratio

    @property
    def name(self) -> str:
        return f"突破{self.window}日高點放量策略"

    @property
    def description(self) -> str:
        return f"收盤價突破過去{self.window}日高點壓力位，且成交量大於5日均量{self.min_vol_ratio}倍。"

    def evaluate(self, df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]:
        if len(df) < self.window + 2:
            return None

        data = TechnicalIndicators.compute_all(df)
        latest = data.iloc[-1]
        prev = data.iloc[-2]

        res_col = f"resistance_{self.window}"
        resistance = latest[res_col]
        close = latest["close"]
        vol_ratio = latest["vol_ratio"]

        # Condition: close above past N-day high and volume surge
        if pd.notnull(resistance) and close > resistance and vol_ratio >= self.min_vol_ratio:
            return StrategySignal(
                ticker=ticker,
                strategy_name=self.name,
                date=str(latest["date"]),
                close_price=float(close),
                message=(
                    f"[{ticker}] 觸發{self.name}！收盤價 {close:.2f} 突破壓力位 "
                    f"{resistance:.2f}，成交量放大至 {vol_ratio:.2f} 倍。"
                ),
                details={
                    "close": float(close),
                    "resistance": float(resistance),
                    "vol_ratio": float(vol_ratio),
                    "volume": float(latest["volume"]),
                },
            )
        return None


class GoldenCrossQuarterMaStrategy(BaseStrategy):
    """Signals when KD shows golden cross while price is sustained above MA60 (Quarter MA)."""

    @property
    def name(self) -> str:
        return "季線之上KD黃金交叉策略"

    @property
    def description(self) -> str:
        return "股價站於季線(MA60)之上，且KD指標低檔黃金交叉 (K向上突破D)。"

    def evaluate(self, df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]:
        if len(df) < 65:
            return None

        data = TechnicalIndicators.compute_all(df)
        latest = data.iloc[-1]
        prev = data.iloc[-2]

        close = latest["close"]
        ma60 = latest["ma_60"]
        k_now, d_now = latest["k"], latest["d"]
        k_prev, d_prev = prev["k"], prev["d"]

        # Golden cross: K crosses above D
        kd_cross = (k_prev <= d_prev) and (k_now > d_now) and (k_now < 80.0)
        above_ma60 = pd.notnull(ma60) and (close >= ma60)

        if kd_cross and above_ma60:
            return StrategySignal(
                ticker=ticker,
                strategy_name=self.name,
                date=str(latest["date"]),
                close_price=float(close),
                message=(
                    f"[{ticker}] 觸發{self.name}！收盤價 {close:.2f} 高於季線(MA60) {ma60:.2f}，"
                    f"KD指標發生黃金交叉 (K:{k_now:.1f}, D:{d_now:.1f})。"
                ),
                details={
                    "close": float(close),
                    "ma60": float(ma60),
                    "k": float(k_now),
                    "d": float(d_now),
                },
            )
        return None


class BullishTrendStrategy(BaseStrategy):
    """Signals strong upward trending equities/ETFs with bullish MA alignment."""

    @property
    def name(self) -> str:
        return "多頭排列強勢趨勢策略"

    @property
    def description(self) -> str:
        return "均線呈多頭排列 (Close > MA20 > MA60) 且股價逼近或創 20 日新高，屬於上升趨勢標的/ETF。"

    def evaluate(self, df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]:
        if len(df) < 65:
            return None

        data = TechnicalIndicators.compute_all(df)
        latest = data.iloc[-1]

        close = latest["close"]
        ma20 = latest["ma_20"]
        ma60 = latest["ma_60"]
        resistance20 = latest["resistance_20"]

        if pd.notnull(ma20) and pd.notnull(ma60) and pd.notnull(resistance20):
            # Bullish trend alignment: Close > MA20 > MA60, and close >= 98% of 20-day high
            if close > ma20 > ma60 and close >= (resistance20 * 0.98):
                return StrategySignal(
                    ticker=ticker,
                    strategy_name=self.name,
                    date=str(latest["date"]),
                    close_price=float(close),
                    message=(
                        f"[{ticker}] 觸發{self.name}！收盤價 {close:.2f} 呈均線多頭排列 "
                        f"(現價 > MA20 {ma20:.2f} > MA60 {ma60:.2f})，逼近波段高點 {resistance20:.2f}。"
                    ),
                    details={
                        "close": float(close),
                        "ma20": float(ma20),
                        "ma60": float(ma60),
                        "resistance": float(resistance20),
                    },
                )
        return None


class Scanner:
    """Executes strategies on historical stock datasets."""

    def __init__(self, strategies: Optional[List[BaseStrategy]] = None):
        if strategies is None:
            self.strategies = [
                BreakoutResistanceStrategy(window=20, min_vol_ratio=1.5),
                GoldenCrossQuarterMaStrategy(),
                BullishTrendStrategy(),
            ]
        else:
            self.strategies = strategies

    def scan_ticker(self, df: pd.DataFrame, ticker: str) -> List[StrategySignal]:
        """Run all strategies against single ticker DataFrame."""
        signals = []
        for strategy in self.strategies:
            sig = strategy.evaluate(df, ticker)
            if sig:
                signals.append(sig)
        return signals
