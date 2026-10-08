"""Main entry point for StockChoice.

Supports one-off execution, dry-run mode, and scheduled daemon mode.
"""

import argparse
import logging
import os
import sys
import time
from typing import List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Lightweight pure-Python .env reader
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("StockChoice")

# Default default watchlist
DEFAULT_TW_TICKERS = ["2330.TW", "2454.TW", "2317.TW", "2382.TW", "2603.TW"]
DEFAULT_US_TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL"]


def fetch_and_update_data(
    tickers: List[str], db: DatabaseManager, twse: TWSEFetcher, yf: YFinanceFetcher
) -> None:
    """Fetch recent data for tickers and store in database."""
    logger.info("Starting data ingestion for %d tickers...", len(tickers))
    for ticker in tickers:
        ticker = ticker.strip().upper()
        try:
            if ticker.endswith(".TW") or ticker.endswith(".TWO"):
                df = twse.fetch_stock_monthly(ticker)
                market = "TW"
            else:
                df = yf.fetch_history(ticker, period="3mo")
                market = "US"

            if not df.empty:
                count = db.save_daily_kline(df, ticker, market)
                logger.info("Updated %s (%s): %d bars saved.", ticker, market, count)
            else:
                logger.warning("No data retrieved for %s.", ticker)
        except Exception as e:
            logger.error("Error updating %s: %s", ticker, e)


def execute_scan(
    tickers: List[str], db: DatabaseManager, scanner: Scanner, notifier: WebhookNotifier, dry_run: bool
) -> None:
    """Read historical data from database, run strategies, and notify."""
    logger.info("Executing technical analysis and strategy scanning...")
    all_signals = []

    for ticker in tickers:
        ticker = ticker.strip().upper()
        df = db.get_daily_kline(ticker, limit=120)
        if df.empty or len(df) < 20:
            logger.warning("Insufficient historical data for %s (rows: %d)", ticker, len(df))
            continue

        signals = scanner.scan_ticker(df, ticker)
        for sig in signals:
            logger.info("MATCH: %s", sig.message)
            db.log_alert(
                ticker=sig.ticker,
                strategy_name=sig.strategy_name,
                trigger_date=sig.date,
                trigger_price=sig.close_price,
                message=sig.message,
            )
            all_signals.append(sig)

    if all_signals:
        logger.info("Total %d signal(s) detected. Dispatching notifications...", len(all_signals))
        notifier.send_signals(all_signals, dry_run=dry_run)
    else:
        logger.info("Scan completed. No strategy conditions met today.")


def run_pipeline(tickers: List[str], dry_run: bool = False) -> None:
    """Execute complete ingestion, analysis, and notification pipeline."""
    db = DatabaseManager()
    twse = TWSEFetcher()
    yf = YFinanceFetcher()
    scanner = Scanner()
    notifier = WebhookNotifier()

    fetch_and_update_data(tickers, db, twse, yf)
    execute_scan(tickers, db, scanner, notifier, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description="StockChoice Automated Stock Scanner")
    parser.add_argument("--dry-run", action="store_true", help="Run without sending real webhook requests")
    parser.add_argument("--once", action="store_true", help="Run pipeline once immediately and exit")
    parser.add_argument("--tickers", type=str, default="", help="Comma-separated stock symbols")
    args = parser.parse_args()

    if args.tickers:
        watchlist = [t.strip() for t in args.tickers.split(",") if t.strip()]
    else:
        watchlist = DEFAULT_TW_TICKERS + DEFAULT_US_TICKERS

    logger.info("StockChoice started. Monitored tickers: %s", watchlist)

    if args.once or args.dry_run:
        logger.info("Running in single execution mode (Dry Run: %s)", args.dry_run)
        run_pipeline(watchlist, dry_run=args.dry_run)
        return

    # Scheduler daemon mode
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        sched_hour = int(os.getenv("SCHEDULE_CRON_HOUR", "15"))
        sched_min = int(os.getenv("SCHEDULE_CRON_MINUTE", "0"))
        tz_str = os.getenv("TZ", "Asia/Taipei")

        scheduler = BlockingScheduler(timezone=tz_str)
        trigger = CronTrigger(hour=sched_hour, minute=sched_min, day_of_week="mon-fri", timezone=tz_str)

        scheduler.add_job(
            run_pipeline,
            trigger=trigger,
            args=[watchlist, False],
            name="daily_stockchoice_pipeline",
        )

        logger.info("Scheduler configured: Mon-Fri at %02d:%02d (%s)", sched_hour, sched_min, tz_str)
        logger.info("Entering daemon loop. Press Ctrl+C to stop.")
        scheduler.start()

    except ImportError:
        logger.warning("apscheduler not installed. Running once and exiting.")
        run_pipeline(watchlist, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
