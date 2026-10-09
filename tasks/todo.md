# StockChoice 開發計畫

本計畫依據 `docs/master_plan.md` 制定，提供給 AI 代理按部就班執行。每完成一項 Task，請勾選並更新 `session_logs`。

## Task 1: 專案基礎環境建置
- [x] 執行 `git init` 並建立標準 `.gitignore`
- [x] 建立 `requirements.txt` (包含 pandas, yfinance, requests, apscheduler, tenacity, pytest)
- [x] 建立 `src/`, `tests/`, `data/` 等目錄結構
- [x] 建立 `.env.example` 模板

## Task 2: 資料庫與資料抓取實作
- [x] 實作 `src/database/db_manager.py` (SQLite 儲存與讀取封裝)
- [x] 實作 `src/data_ingestion/twse_fetcher.py` (台股盤後 API)
- [x] 實作 `src/data_ingestion/yfinance_fetcher.py` (美股 API)

## Task 3: 技術指標與策略實作
- [x] 實作 `src/ta_engine/indicators.py` (Pandas MA 與 Rolling 極值計算)
- [x] 實作 `src/scanner/strategy.py` (封裝條件篩選邏輯，如突破 20 日極值)

## Task 4: 測試與驗證 (Verification)
- [x] 撰寫 `tests/test_indicators.py` (測試技術指標算式正確性)
- [x] 撰寫 `tests/test_fetchers.py` (Mock 測試資料獲取邏輯)
- [x] 執行 `pytest` / `unittest` 確保全數通過

## Task 5: 通知推播與主程式排程
- [x] 實作 `src/notifier/webhook.py` (Discord/Line 訊息格式封裝)
- [x] 實作 `src/main.py` 整合上述模組，並加上 `--dry-run` 參數支援
- [x] 在 `main.py` 註冊 APScheduler 定時排程 (如每日 15:00 執行)

## Task 6: 部署與手冊撰寫
- [x] 撰寫 `Dockerfile`
- [x] 撰寫 `docker-compose.yml` (設定 TZ 與 Volume)
- [x] 撰寫 `README.md` (使用者部署手冊)
- [x] 撰寫 `DEVELOPER.md` (開發者擴充指南)

## Task 7: GitHub Pages 網頁儀表板與自動化發布
- [x] 實作 `web/index.html` 響應式前端 (支援手機大字體、新手/專業模式切換、LocalStorage 存股試算與 TradingView 圖表)
- [x] 實作 `generate_web_data.py` 盤後數據生成器 (產出 `web/data.json`)
- [x] 撰寫 `.github/workflows/deploy.yml` GitHub Actions 自動化部署工作流 (平日 16:00 定時排程)

---

## 成果審查 (Review & Verification)
- [x] **單元測試全數通過**：執行 `python3 -m unittest discover -s tests -p "test_*.py"`，10 個測試案例 (指標計算、極值通道、TWSE 轉換、Mock 解析、資料庫 CRUD) 全部通過。
- [x] **CLI 功能驗證**：驗證 `main.py --help` 正確解析 `--dry-run`、`--once` 與 `--tickers` 參數。
- [x] **容器化與 NAS 準備**：已配置 Dockerfile 及 docker-compose.yml，包含 `./data:/app/data` 持久化磁碟映射與 `TZ=Asia/Taipei`。
- [x] **文件齊備**：已產出完整的使用手冊 `README.md` 與開發者擴充指南 `DEVELOPER.md`。
