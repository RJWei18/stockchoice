# StockChoice 開發者擴充與維護指南

本文件供開發者或接手之 AI 模型參考，說明架構規範與新增自訂指標與策略的標準流程。

---

## 專案模組架構

```text
stockchoice/
├── src/
│   ├── database/db_manager.py     # SQLite 抽象層，包含連線池管理與歷史查詢
│   ├── data_ingestion/            # 數據源實作 (twse_fetcher.py, yfinance_fetcher.py)
│   ├── ta_engine/indicators.py    # 純 Pandas 向量化指標運算 (MA, 極值通道, KD, MACD, RSI)
│   ├── scanner/strategy.py        # 策略介面 (BaseStrategy) 與篩選執行器 (Scanner)
│   ├── notifier/webhook.py        # Webhook 封裝 (Discord Embeds / Generic JSON)
│   └── main.py                    # 流程整合與 APScheduler 排程主進入點
├── tests/                         # 單元測試集
```

---

## 如何新增自訂策略

所有的策略均需繼承 `src.scanner.strategy.BaseStrategy`，並實作以下三個屬性與方法：

1. `name`: 策略名稱 (顯示於推播標題)
2. `description`: 規則說明
3. `evaluate(df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]`:
   - 接收已經包含技術指標的歷史 DataFrame。
   - 若符合買進/注意條件，回傳 `StrategySignal` 物件。
   - 若不符合條件，回傳 `None`。

### 範例：新增「均線三陽開泰策略 (MA 糾結後向上突破)」
```python
from src.scanner.strategy import BaseStrategy, StrategySignal

class TripleMaBreakoutStrategy(BaseStrategy):
    @property
    def name(self) -> str:
        return "三均線糾結多頭突破策略"

    @property
    def description(self) -> str:
        return "5日、10日、20日均線糾結後，今日收盤價同時站上三條均線並帶量。"

    def evaluate(self, df: pd.DataFrame, ticker: str) -> Optional[StrategySignal]:
        if len(df) < 25:
            return None
            
        latest = df.iloc[-1]
        close = latest["close"]
        ma5 = latest["ma_5"]
        ma10 = latest["ma_10"]
        ma20 = latest["ma_20"]
        
        # 條件：收盤價突破 MA5, MA10, MA20
        if close > ma5 and close > ma10 and close > ma20 and latest["vol_ratio"] >= 1.5:
            return StrategySignal(
                ticker=ticker,
                strategy_name=self.name,
                date=str(latest["date"]),
                close_price=float(close),
                message=f"[{ticker}] 觸發{self.name}！收盤價 {close:.2f} 同步突破短期均線糾結區。",
                details={"close": close, "ma5": ma5, "ma10": ma10, "ma20": ma20}
            )
        return None
```

註冊新策略只需在 `src/scanner/strategy.py` 的 `Scanner.__init__` 加入實例：
```python
self.strategies.append(TripleMaBreakoutStrategy())
```

---

## 測試撰寫與驗證標準
每次修改或新增模組後，必須在 `tests/` 下加入或更新對應測試，並執行：
```bash
python -m unittest discover -s tests -p "test_*.py"
```
確保測試全數通過方可提交 Commit。
