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

## Task 8: K線時間軸優化、MACD 指標圖與籌碼面數據實作
- [x] 擴充 `generate_web_data.py`：產出 MACD（DIF, Signal, OSC）歷史序列、最新 MACD 指標與三大法人籌碼面（外資、投信、自營商買賣超與籌碼集中度摘要）
- [x] 優化前端 K線圖表時間軸與浮動游標：在 Modal 頂部顯示最新 K 線確切日期（如 2026-10-08）與 OHLCV/均線數值；配置 `rightOffset` 與游標 crosshair 懸浮資訊，解除時間軸僅顯示「8月」的視覺誤解
- [x] 實作 K線 Modal 多圖表/分頁切換：提供「K線均線 (MA20/MA60)」、「MACD 擺盪指標」、「成交量」與「籌碼面 (三大法人動態)」互動切換
- [x] 卡片展開與表格視圖補強：於卡片詳細資訊加入 MACD 與籌碼面摘要，直觀呈現多空結構
- [x] 執行資料重產與驗證：執行 `generate_web_data.py` 產生最新 `web/data.json`，跑單元測試確保全數通過，並 push 至 GitHub

## Task 9: 股票/ETF 搜尋功能、愛心自選清單與庫存定期定額定位切換
- [x] 擴展台美股監控標的群 (`generate_web_data.py`)：將熱門台股、熱門高息/市值型 ETF 與美股標的擴充至監控池（共 64 檔），完整產出 AI 總結、殖利率、價量比與籌碼面
- [x] 前端實作即時搜尋功能 (`web/index.html`)：在頁面加入「🔍 搜尋股票代碼或名稱」輸入框，支援即時關鍵字模糊過濾
- [x] 實作愛心收藏（自選股）功能：每檔標的卡片與表格加入 ❤️ 收藏按鈕，狀態保存於 `localStorage ('sc_favorites')`，並提供「全部標的 / ❤️ 我的自選 / ETF / 個股」快速過濾標籤
- [x] 重新定位定期定額與存股頁籤：明確界定為「真實持股與扣款追蹤」，僅呈現使用者實際已買進的庫存股數、平均買進成本、現值損益與預估年領股利
- [x] 驗證並發布：重跑資料生成器、執行單元測試並部署至 GitHub Pages

---

## 成果審查 (Review & Verification)
- [x] **單元測試全數通過**：執行 `python3 -m unittest discover -s tests -p "test_*.py"`，10 個測試案例 (指標計算、極值通道、TWSE 轉換、Mock 解析、資料庫 CRUD) 全部通過。
- [x] **CLI 功能驗證**：驗證 `main.py --help` 正確解析 `--dry-run`、`--once` 與 `--tickers` 參數。
- [x] **容器化與 NAS 準備**：已配置 Dockerfile 及 docker-compose.yml，包含 `./data:/app/data` 持久化磁碟映射與 `TZ=Asia/Taipei`。
- [x] **文件齊備**：已產出完整的使用手冊 `README.md` 與開發者擴充指南 `DEVELOPER.md`。
