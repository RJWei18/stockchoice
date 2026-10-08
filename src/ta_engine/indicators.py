"""Technical Analysis Engine.

Calculates Moving Averages, Donchian Channels (Support/Resistance),
RSI, KD, and MACD using pure pandas vectorization.
"""

from typing import List, Optional
import numpy as np
import pandas as pd


class TechnicalIndicators:
    """Computes technical indicators on daily OHLCV DataFrames."""

    @staticmethod
    def add_moving_averages(df: pd.DataFrame, windows: Optional[List[int]] = None) -> pd.DataFrame:
        """Add Simple Moving Averages for specified windows."""
        if windows is None:
            windows = [5, 10, 20, 60]
        out = df.copy()
        for w in windows:
            out[f"ma_{w}"] = out["close"].rolling(window=w, min_periods=1).mean()
        return out

    @staticmethod
    def add_donchian_channels(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Add Donchian Channels representing dynamic resistance (upper) and support (lower).

        Uses shift(1) so today's breakout is tested against the past N days.
        """
        out = df.copy()
        out[f"resistance_{window}"] = out["high"].shift(1).rolling(window=window, min_periods=1).max()
        out[f"support_{window}"] = out["low"].shift(1).rolling(window=window, min_periods=1).min()
        out[f"mid_band_{window}"] = (out[f"resistance_{window}"] + out[f"support_{window}"]) / 2.0
        return out

    @staticmethod
    def add_volume_metrics(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Add volume moving average and volume surge ratio."""
        out = df.copy()
        vol_ma = out["volume"].shift(1).rolling(window=window, min_periods=1).mean()
        out[f"vol_ma_{window}"] = vol_ma
        out["vol_ratio"] = np.where(vol_ma > 0, out["volume"] / vol_ma, 1.0)
        return out

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index (RSI)."""
        out = df.copy()
        delta = out["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        out[f"rsi_{period}"] = 100 - (100 / (1 + rs))
        out[f"rsi_{period}"] = out[f"rsi_{period}"].fillna(50.0)
        return out

    @staticmethod
    def add_kd(df: pd.DataFrame, period: int = 9) -> pd.DataFrame:
        """Add Stochastic Oscillator (KD indicator)."""
        out = df.copy()
        lowest_low = out["low"].rolling(window=period, min_periods=1).min()
        highest_high = out["high"].rolling(window=period, min_periods=1).max()

        denom = highest_high - lowest_low
        rsv = np.where(denom > 0, (out["close"] - lowest_low) / denom * 100.0, 50.0)

        k_vals = []
        d_vals = []
        k_prev = 50.0
        d_prev = 50.0

        for r in rsv:
            k = (2.0 / 3.0) * k_prev + (1.0 / 3.0) * r
            d = (2.0 / 3.0) * d_prev + (1.0 / 3.0) * k
            k_vals.append(k)
            d_vals.append(d)
            k_prev = k
            d_prev = d

        out["k"] = k_vals
        out["d"] = d_vals
        return out

    @staticmethod
    def add_macd(
        df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.DataFrame:
        """Add Moving Average Convergence Divergence (MACD)."""
        out = df.copy()
        ema_fast = out["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = out["close"].ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        macd_signal = dif.ewm(span=signal, adjust=False).mean()
        osc = dif - macd_signal

        out["macd_dif"] = dif
        out["macd_signal"] = macd_signal
        out["macd_osc"] = osc
        return out

    @classmethod
    def compute_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all core technical indicators on the given DataFrame."""
        if df.empty:
            return df
        res = cls.add_moving_averages(df, [5, 10, 20, 60])
        res = cls.add_donchian_channels(res, window=20)
        res = cls.add_volume_metrics(res, window=5)
        res = cls.add_rsi(res, period=14)
        res = cls.add_kd(res, period=9)
        res = cls.add_macd(res)
        return res
