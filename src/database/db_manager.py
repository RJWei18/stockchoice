"""SQLite Database Manager for StockChoice.

Handles schema initialization, batch insertion, and historical data retrieval.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Optional
import pandas as pd


class DatabaseManager:
    """Manages SQLite operations for stock market daily K-line data."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with database file path."""
        if db_path is None:
            db_path = os.getenv("DB_PATH", "data/stock.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a managed SQLite database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize required database tables if not existing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_kline (
                    ticker TEXT NOT NULL,
                    market TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    updated_at TEXT,
                    PRIMARY KEY (ticker, date)
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_kline_ticker_date 
                ON daily_kline (ticker, date)
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    trigger_date TEXT NOT NULL,
                    trigger_price REAL,
                    message TEXT,
                    created_at TEXT
                )
                """
            )
            conn.commit()

    def save_daily_kline(self, df: pd.DataFrame, ticker: str, market: str) -> int:
        """Upsert daily K-line records from pandas DataFrame.

        Expected DataFrame columns (case-insensitive):
        date, open, high, low, close, volume.

        Returns:
            Number of records inserted/updated.
        """
        if df.empty:
            return 0

        # Standardize column names to lowercase
        norm_df = df.copy()
        norm_df.columns = [str(c).strip().lower() for c in norm_df.columns]

        required_cols = {"date", "open", "high", "low", "close", "volume"}
        if not required_cols.issubset(set(norm_df.columns)):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        now_str = datetime.now().isoformat()
        records = []
        for _, row in norm_df.iterrows():
            records.append(
                (
                    str(ticker).strip().upper(),
                    str(market).strip().upper(),
                    str(row["date"]).strip(),
                    float(row["open"]) if pd.notnull(row["open"]) else None,
                    float(row["high"]) if pd.notnull(row["high"]) else None,
                    float(row["low"]) if pd.notnull(row["low"]) else None,
                    float(row["close"]) if pd.notnull(row["close"]) else None,
                    float(row["volume"]) if pd.notnull(row["volume"]) else None,
                    now_str,
                )
            )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO daily_kline (
                    ticker, market, date, open, high, low, close, volume, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ticker, date) DO UPDATE SET
                    market=excluded.market,
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    updated_at=excluded.updated_at
                """,
                records,
            )
            conn.commit()

        return len(records)

    def get_daily_kline(self, ticker: str, limit: int = 120) -> pd.DataFrame:
        """Retrieve historical K-line data for a given ticker, ordered ascending by date.

        Returns:
            DataFrame with columns: date, open, high, low, close, volume.
        """
        ticker_clean = str(ticker).strip().upper()
        with self.get_connection() as conn:
            query = """
                SELECT date, open, high, low, close, volume
                FROM (
                    SELECT date, open, high, low, close, volume
                    FROM daily_kline
                    WHERE ticker = ?
                    ORDER BY date DESC
                    LIMIT ?
                )
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn, params=(ticker_clean, limit))
        return df

    def get_all_tickers(self, market: Optional[str] = None) -> List[str]:
        """Get distinct tickers stored in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if market:
                cursor.execute(
                    "SELECT DISTINCT ticker FROM daily_kline WHERE market = ? ORDER BY ticker",
                    (market.strip().upper(),),
                )
            else:
                cursor.execute("SELECT DISTINCT ticker FROM daily_kline ORDER BY ticker")
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def log_alert(
        self,
        ticker: str,
        strategy_name: str,
        trigger_date: str,
        trigger_price: float,
        message: str,
    ) -> None:
        """Record an alert event."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alert_logs (
                    ticker, strategy_name, trigger_date, trigger_price, message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ticker.strip().upper(),
                    strategy_name,
                    trigger_date,
                    trigger_price,
                    message,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
