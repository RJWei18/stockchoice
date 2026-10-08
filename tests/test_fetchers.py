"""Unit tests for Data Ingestion fetchers and Database integration."""

import os
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.database.db_manager import DatabaseManager
from src.data_ingestion.twse_fetcher import TWSEFetcher
from src.data_ingestion.yfinance_fetcher import YFinanceFetcher


class TestDataFetchers(unittest.TestCase):
    """Test suite for data ingestion and normalization."""

    def setUp(self):
        self.twse = TWSEFetcher()
        self.yf = YFinanceFetcher()
        self.test_db_path = "data/test_integration.db"
        self.db = DatabaseManager(self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_twse_date_conversion(self):
        """Verify ROC year to AD year conversion."""
        self.assertEqual(self.twse._convert_roc_date_to_ad("113/05/02"), "2024-05-02")
        self.assertEqual(self.twse._convert_roc_date_to_ad("112/12/31"), "2023-12-31")

    def test_clean_number(self):
        """Verify string numbers with commas and dashes are parsed properly."""
        self.assertEqual(self.twse._clean_number("1,234.50"), 1234.50)
        self.assertIsNone(self.twse._clean_number("--"))
        self.assertIsNone(self.twse._clean_number(""))

    @patch("src.data_ingestion.twse_fetcher.requests.Session.get")
    def test_twse_fetch_mock(self, mock_get):
        """Verify TWSE fetcher handles mock JSON API response correctly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "stat": "OK",
            "data": [
                ["113/05/02", "10,000,000", "5,000,000,000", "780.0", "795.0", "778.0", "790.0", "+10.0", "25,000"],
                ["113/05/03", "12,000,000", "6,000,000,000", "792.0", "800.0", "790.0", "798.0", "+8.0", "28,000"],
            ],
        }
        mock_get.return_value = mock_resp

        df = self.twse.fetch_stock_monthly("2330.TW")
        self.assertEqual(len(df), 2)
        self.assertEqual(df["date"].iloc[0], "2024-05-02")
        self.assertEqual(df["close"].iloc[0], 790.0)
        self.assertEqual(df["volume"].iloc[0], 10000000.0)

    @patch("src.data_ingestion.yfinance_fetcher.requests.Session.get")
    def test_yfinance_chart_api_mock(self, mock_get):
        """Verify Yahoo Finance Chart API mock parser."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1714608000],  # 2024-05-02 approx
                        "indicators": {
                            "quote": [
                                {
                                    "open": [170.0],
                                    "high": [175.0],
                                    "low": [169.0],
                                    "close": [173.0],
                                    "volume": [50000000],
                                }
                            ]
                        },
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        df = self.yf._fetch_via_chart_api("AAPL")
        self.assertEqual(len(df), 1)
        self.assertEqual(df["close"].iloc[0], 173.0)
        self.assertEqual(df["open"].iloc[0], 170.0)

    def test_db_upsert_and_query(self):
        """Verify full round-trip saving and retrieving from database."""
        df = pd.DataFrame(
            [
                {"date": "2024-05-01", "open": 100, "high": 105, "low": 99, "close": 104, "volume": 1000},
                {"date": "2024-05-02", "open": 104, "high": 108, "low": 103, "close": 107, "volume": 1200},
            ]
        )
        saved = self.db.save_daily_kline(df, "2330.TW", "TW")
        self.assertEqual(saved, 2)

        res = self.db.get_daily_kline("2330.TW")
        self.assertEqual(len(res), 2)
        self.assertEqual(res["close"].iloc[1], 107.0)


if __name__ == "__main__":
    unittest.main()
