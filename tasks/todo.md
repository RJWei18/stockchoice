# StockChoice 開發計畫

本計畫依據 `docs/master_plan.md` 制定，提供給 AI 代理按部就班執行。每完成一項 Task，請勾選並更新 `session_logs`。

## Task 1: 專案基礎環境建置
- [x] 執行 `git init` 並建立標準 `.gitignore`
- [x] 建立 `requirements.txt` (包含 pandas, yfinance, requests, apscheduler, tenacity, pytest)
- [x] 建立 `src/`, `tests/`, `data/` 等目錄結構
- [x] 建立 `.env.example` 模板

## Task 2: 資料庫與資料抓取實作
- [ ] 實作 `src/database/db_manager.py` (SQLite 儲存與讀取封裝)
- [ ] 實作 `src/data_ingestion/twse_fetcher.py` (台股盤後 API)
- [ ] 實作 `src/data_ingestion/yfinance_fetcher.py` (美股 API)

## Task 3: 技術指標與策略實作
- [ ] 實作 `src/ta_engine/indicators.py` (Pandas MA 與 Rolling 極值計算)
- [ ] 實作 `src/scanner/strategy.py` (封裝條件篩選邏輯，如突破 20 日極值)

## Task 4: 測試與驗證 (Verification)
- [ ] 撰寫 `tests/test_indicators.py` (測試技術指標算式正確性)
- [ ] 撰寫 `tests/test_fetchers.py` (Mock 測試資料獲取邏輯)
- [ ] 執行 `pytest` 確保全數通過

## Task 5: 通知推播與主程式排程
- [ ] 實作 `src/notifier/webhook.py` (Discord/Line 訊息格式封裝)
- [ ] 實作 `src/main.py` 整合上述模組，並加上 `--dry-run` 參數支援
- [ ] 在 `main.py` 註冊 APScheduler 定時排程 (如每日 15:00 執行)

## Task 6: 部署與手冊撰寫
- [ ] 撰寫 `Dockerfile`
- [ ] 撰寫 `docker-compose.yml` (設定 TZ 與 Volume)
- [ ] 撰寫 `README.md` (使用者部署手冊)
- [ ] 撰寫 `DEVELOPER.md` (開發者擴充指南)
