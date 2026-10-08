"""Webhook Notification Module.

Supports Discord Webhook and Generic HTTP Push notifications with dry-run support.
"""

import json
import logging
import os
from typing import List, Optional
import requests
from src.scanner.strategy import StrategySignal

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Dispatches strategy screening alerts via Webhook."""

    def __init__(self, webhook_url: Optional[str] = None, platform: str = "discord"):
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_URL")
        self.platform = (platform or os.getenv("NOTIFY_PLATFORM", "discord")).lower()
        self.session = requests.Session()

    def send_signals(self, signals: List[StrategySignal], dry_run: bool = False) -> bool:
        """Send a batch of strategy alerts to the configured webhook."""
        if not signals:
            logger.info("No signals to dispatch.")
            return True

        if dry_run or not self.webhook_url:
            logger.info("[DRY-RUN / NO-URL] Intercepted %d signals notification:", len(signals))
            for sig in signals:
                logger.info("  -> %s", sig.message)
            return True

        if self.platform == "discord":
            return self._send_discord(signals)
        else:
            return self._send_generic(signals)

    def _send_discord(self, signals: List[StrategySignal]) -> bool:
        """Send rich embeds to Discord webhook."""
        embeds = []
        for s in signals[:10]:  # Limit to 10 embeds per message (Discord limit)
            fields = [
                {"name": "策略名稱", "value": s.strategy_name, "inline": True},
                {"name": "收盤價", "value": f"{s.close_price:.2f}", "inline": True},
                {"name": "觸發日期", "value": s.date, "inline": True},
            ]
            for k, v in s.details.items():
                if k not in ("close", "volume"):
                    fields.append({"name": k, "value": f"{v:.2f}", "inline": True})

            embeds.append(
                {
                    "title": f"📈 股票訊號通知：{s.ticker}",
                    "description": s.message,
                    "color": 0x2ECC71,  # Green
                    "fields": fields,
                }
            )

        payload = {
            "content": f"🎯 **StockChoice 盤後篩選報告** (共 {len(signals)} 檔符合條件)",
            "embeds": embeds,
        }

        try:
            resp = self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            logger.info("Successfully pushed %d signals to Discord.", len(signals))
            return True
        except Exception as e:
            logger.error("Failed to push webhook to Discord: %s", e)
            return False

    def _send_generic(self, signals: List[StrategySignal]) -> bool:
        """Send plain text or standard JSON to generic webhook."""
        lines = [f"StockChoice 盤後篩選報告 (共 {len(signals)} 檔):"]
        for s in signals:
            lines.append(f"- {s.message}")

        payload = {"message": "\n".join(lines)}
        try:
            resp = self.session.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error("Failed to dispatch generic webhook: %s", e)
            return False
