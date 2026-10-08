"""US and Global Stock Data Fetcher.

Fetches daily OHLCV bars using yfinance if available, with a resilient fallback
to Yahoo Finance REST Chart API.
"""

import logging
import time
from datetime import datetime
from typing import Optional
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class YFinanceFetcher:
    """Fetcher for US and international equities."""

    def __init__(self, timeout: int = 15, max_retries: int = 3, retry_delay: float = 2.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            }
        )

    def fetch_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        """Fetch historical daily bars for a ticker.

        Args:
            ticker: Stock symbol, e.g. 'AAPL', 'NVDA', 'TSLA'.
            period: Range period such as '1mo', '3mo', '6mo', '1y'.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume.
        """
        clean_ticker = ticker.strip().upper()

        # Attempt 1: Try importing yfinance if installed in runtime
        try:
            import yfinance as yf

            for attempt in range(1, self.max_retries + 1):
                try:
                    df = yf.download(
                        clean_ticker,
                        period=period,
                        interval="1d",
                        progress=False,
                        auto_adjust=False,
                    )
                    if df is not None and not df.empty:
                        df = df.reset_index()
                        # Rename columns
                        col_map = {}
                        for c in df.columns:
                            c_str = str(c[0] if isinstance(c, tuple) else c).strip().lower()
                            if "date" in c_str:
                                col_map[c] = "date"
                            elif "open" in c_str:
                                col_map[c] = "open"
                            elif "high" in c_str:
                                col_map[c] = "high"
                            elif "low" in c_str:
                                col_map[c] = "low"
                            elif "close" in c_str and "adj" not in c_str:
                                col_map[c] = "close"
                            elif "volume" in c_str:
                                col_map[c] = "volume"

                        df = df.rename(columns=col_map)
                        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
                        needed = ["date", "open", "high", "low", "close", "volume"]
                        if set(needed).issubset(set(df.columns)):
                            return df[needed].dropna(subset=["close"]).sort_values("date").reset_index(drop=True)
                except Exception as e:
                    logger.warning("yfinance download attempt %d failed for %s: %s", attempt, clean_ticker, e)
                    time.sleep(self.retry_delay)
        except ImportError:
            logger.info("yfinance package not detected. Using direct Yahoo Finance Chart API fallback.")

        # Attempt 2: Fallback to Yahoo Finance v8 Chart API
        return self._fetch_via_chart_api(clean_ticker, period)

    def _fetch_via_chart_api(self, ticker: str, range_str: str = "3mo") -> pd.DataFrame:
        """Direct REST call to Yahoo Finance Chart API."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {
            "range": range_str,
            "interval": "1d",
            "indicators": "quote",
            "includeTimestamps": "true",
        }

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()

                chart = data.get("chart", {})
                results = chart.get("result")
                if not results or len(results) == 0:
                    logger.warning("No chart result found for %s", ticker)
                    return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

                res = results[0]
                timestamps = res.get("timestamp", [])
                indicators = res.get("indicators", {}).get("quote", [{}])[0]

                opens = indicators.get("open", [])
                highs = indicators.get("high", [])
                lows = indicators.get("low", [])
                closes = indicators.get("close", [])
                volumes = indicators.get("volume", [])

                rows = []
                for ts, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, volumes):
                    if c is None or pd.isna(c):
                        continue
                    dt_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    rows.append(
                        {
                            "date": dt_str,
                            "open": float(o) if o is not None else None,
                            "high": float(h) if h is not None else None,
                            "low": float(l) if l is not None else None,
                            "close": float(c),
                            "volume": float(v) if v is not None else 0.0,
                        }
                    )

                df = pd.DataFrame(rows)
                if not df.empty:
                    df = df.sort_values("date").reset_index(drop=True)
                return df

            except Exception as e:
                last_err = e
                logger.warning(
                    "Yahoo Chart API attempt %d/%d failed for %s: %s",
                    attempt,
                    self.max_retries,
                    ticker,
                    e,
                )
                time.sleep(self.retry_delay)

        logger.error("Failed to fetch data for %s: %s", ticker, last_err)
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
