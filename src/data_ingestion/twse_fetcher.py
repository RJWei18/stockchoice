"""TWSE Data Fetcher for Taiwan Stock Exchange.

Provides functions to fetch daily market quotes and individual stock historical data.
"""

import logging
import time
from datetime import datetime
from typing import Optional
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class TWSEFetcher:
    """Fetches end-of-day data from TWSE public endpoints."""

    BASE_URL_STOCK_DAY = "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY"
    BASE_URL_ALL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

    def __init__(self, timeout: int = 10, max_retries: int = 3, retry_delay: float = 2.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
            }
        )

    def _convert_roc_date_to_ad(self, roc_date_str: str) -> str:
        """Convert Republic of China date string (e.g. '113/05/02') to ISO date ('2024-05-02')."""
        parts = roc_date_str.strip().split("/")
        if len(parts) == 3:
            year = int(parts[0]) + 1911
            month = int(parts[1])
            day = int(parts[2])
            return f"{year:04d}-{month:02d}-{day:02d}"
        return roc_date_str.strip()

    def _clean_number(self, val: any) -> Optional[float]:
        """Convert formatted string numbers (e.g. '1,234.50' or '--') to float."""
        if val is None or pd.isna(val):
            return None
        s = str(val).replace(",", "").strip()
        if s in ("", "--", "X0.00", "除息", "除權"):
            return None
        try:
            return float(s)
        except ValueError:
            return None

    def fetch_stock_monthly(self, ticker: str, date_str: Optional[str] = None) -> pd.DataFrame:
        """Fetch monthly trading data for a specific stock ticker.

        Args:
            ticker: Stock symbol, e.g. '2330' or '2330.TW'.
            date_str: YYYYMMDD string (defaults to today).

        Returns:
            DataFrame with columns: date, open, high, low, close, volume.
        """
        clean_ticker = ticker.replace(".TW", "").replace(".TWO", "").strip()
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")

        params = {
            "response": "json",
            "date": date_str,
            "stockNo": clean_ticker,
        }

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(self.BASE_URL_STOCK_DAY, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()

                if data.get("stat") != "OK" or "data" not in data:
                    logger.warning(
                        "TWSE returned non-OK status: %s for %s", data.get("stat"), clean_ticker
                    )
                    return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

                rows = []
                for item in data["data"]:
                    # TWSE fields:
                    # [0] 日期, [1] 成交股數, [2] 成交金額, [3] 開盤價, [4] 最高價, [5] 最低價, [6] 收盤價, [7] 漲跌價差, [8] 成交筆數
                    date_ad = self._convert_roc_date_to_ad(str(item[0]))
                    volume = self._clean_number(item[1])
                    open_p = self._clean_number(item[3])
                    high_p = self._clean_number(item[4])
                    low_p = self._clean_number(item[5])
                    close_p = self._clean_number(item[6])

                    rows.append(
                        {
                            "date": date_ad,
                            "open": open_p,
                            "high": high_p,
                            "low": low_p,
                            "close": close_p,
                            "volume": volume,
                        }
                    )

                df = pd.DataFrame(rows)
                df.dropna(subset=["close"], inplace=True)
                return df

            except Exception as e:
                last_err = e
                logger.warning(
                    "Attempt %d/%d failed for TWSE stock %s: %s",
                    attempt,
                    self.max_retries,
                    clean_ticker,
                    e,
                )
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        logger.error("All retries exhausted for TWSE stock %s. Last error: %s", clean_ticker, last_err)
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

    def fetch_all_daily_quotes(self) -> pd.DataFrame:
        """Fetch today's full market daily quotes from TWSE OpenAPI."""
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(self.BASE_URL_ALL, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()

                if not isinstance(data, list):
                    return pd.DataFrame()

                today_str = datetime.now().strftime("%Y-%m-%d")
                rows = []
                for item in data:
                    code = item.get("Code", "").strip()
                    open_p = self._clean_number(item.get("OpeningPrice"))
                    high_p = self._clean_number(item.get("HighestPrice"))
                    low_p = self._clean_number(item.get("LowestPrice"))
                    close_p = self._clean_number(item.get("ClosingPrice"))
                    vol = self._clean_number(item.get("TradeVolume"))

                    if code and close_p is not None:
                        rows.append(
                            {
                                "ticker": f"{code}.TW",
                                "name": item.get("Name", "").strip(),
                                "date": today_str,
                                "open": open_p,
                                "high": high_p,
                                "low": low_p,
                                "close": close_p,
                                "volume": vol,
                            }
                        )

                return pd.DataFrame(rows)

            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        logger.error("Failed to fetch TWSE all daily quotes: %s", last_err)
        return pd.DataFrame()

    def fetch_fundamentals(self, ticker: str) -> dict:
        """Fetch P/E ratio, Dividend Yield, and P/B ratio for a TWSE stock.

        Returns:
            dict with keys: 'pe_ratio', 'dividend_yield', 'pb_ratio'.
        """
        clean_ticker = ticker.replace(".TW", "").replace(".TWO", "").strip()

        # Benchmarked approximate annualized dividend yields for popular TW ETFs
        etf_yields = {
            "0050": 3.85,
            "0056": 7.45,
            "00878": 8.80,
            "00919": 10.95,
            "00929": 9.20,
            "00713": 6.80,
            "006208": 3.75,
            "00940": 6.20,
            "00939": 6.50,
            "00915": 9.40,
            "00881": 5.20,
            "00757": 1.20,
            "00679B": 4.35,
            "00687B": 4.40,
        }
        if clean_ticker in etf_yields:
            return {"dividend_yield": etf_yields[clean_ticker], "pe_ratio": None, "pb_ratio": None}

        # Query official TWSE OpenAPI full market list
        if not hasattr(self, "_cached_bwibbu") or self._cached_bwibbu is None:
            try:
                resp = self.session.get("https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", timeout=self.timeout)
                if resp.status_code == 200:
                    self._cached_bwibbu = {item.get("Code"): item for item in resp.json() if "Code" in item}
            except Exception as e:
                logger.warning("Failed to fetch BWIBBU_ALL: %s", e)
                self._cached_bwibbu = {}

        if hasattr(self, "_cached_bwibbu") and self._cached_bwibbu and clean_ticker in self._cached_bwibbu:
            item = self._cached_bwibbu[clean_ticker]
            return {
                "dividend_yield": self._clean_number(item.get("DividendYield")),
                "pe_ratio": self._clean_number(item.get("PEratio")),
                "pb_ratio": self._clean_number(item.get("PBratio")),
            }

        # Fallback to single stock endpoint
        url = "https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d"
        params = {
            "response": "json",
            "date": datetime.now().strftime("%Y%m%d"),
            "stockNo": clean_ticker,
        }
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("stat") == "OK" and "data" in data and len(data["data"]) > 0:
                    latest = data["data"][-1]
                    # TWSE fields: [0] 日期, [1] 殖利率(%), [2] 股利年度, [3] 本益比, [4] 股價淨值比
                    return {
                        "dividend_yield": self._clean_number(latest[1]),
                        "pe_ratio": self._clean_number(latest[3]),
                        "pb_ratio": self._clean_number(latest[4]),
                    }
        except Exception as e:
            logger.warning("Failed to fetch TWSE fundamentals for %s: %s", clean_ticker, e)

        return {"dividend_yield": None, "pe_ratio": None, "pb_ratio": None}

