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

## Task 10: 策略回測系統（核心引擎、方式 A 網頁實驗室、方式 B Telegram 對話）
- [x] 實作核心回測引擎 (`src/backtest/engine.py` & `metrics.py`)：支援自訂跌幅買進、漲幅停利、停損閥值、交易成本扣除與 MDD / 勝率 / CAGR 指標運算
- [x] 撰寫單元測試 (`tests/test_backtest.py`)：驗證撮合邏輯、資產淨值曲線計算與交易次數統計
- [x] 整合方式 B (Telegram Albedo 機器人)：於 `Albedo/stock_service.py` 與 `bot.py` 實作回測查詢介面與 `/backtest` 格式化輸出
- [x] 實作方式 A (網頁版策略回測實驗室)：於 `web/index.html` 新增回測專用分頁，提供參數自訂滑桿、績效指標卡與 Canvas 淨值走勢曲線（對比 Buy & Hold）
- [x] 同步架構手冊與進度：更新 `Albedo/design_spec.md`、`Albedo/progress.md` 與 `session_logs/`，並執行全模組驗證

## Task 11: 推薦清單信心評級強化與一般標的「查看 AI 評級」深度診斷功能
- [x] 強化精選推薦清單：預設清楚標註 AI 信心評級標籤、星級與信心等級
- [x] 實作全盤指標 AI 綜合評語生成器 (`generateAiDiagnosis`)：統整均線結構、MACD/KD/RSI 擺盪指標、三大法人/機構籌碼動態、價量比與估值位階，產出專業深度量化診斷與關鍵點位操作指引
- [x] 一般台美股卡片新增「查看 AI 評級」按鈕與動態展開診斷面板：具備運算反饋狀態、可隨時展開/收合
- [x] 表格視圖 (Table View) 支援 AI 評級診斷：操作欄新增 AI 評級觸發按鈕，並提供全螢幕 AI 診斷彈窗 Modal
- [x] 驗證並發布：本機測試前端響應式排版與互動、執行現有單元測試、commit 並 push 觸發 GitHub Actions 部署

## Task 12: 盤後真實 LLM 深度分析批次生成機制 (待辦)
- [ ] 整合 Gemini / Claude API 於 `generate_web_data.py` 盤後產線
- [ ] 每日 15:30 盤後批次生成各標的專業自然語言評論並寫入快取，防範前端金鑰外洩與額度被刷爆

## Task 13: 盤中即時行情資料源與更新機制 (待辦)
- [ ] 串接台股盤中即時行情（TWSE MIS / Fugle Market API / 券商 Shioaji SDK）
- [ ] 盤中開盤時間定時或手動拉取最新成交價與漲跌幅

## Task 14: 家庭成員雲端跨裝置自選與持股同步機制 (待辦)
- [ ] 評估輕量代碼同步（Cloudflare KV / Supabase 免費層）或 Google OAuth 登入隔離方案
- [ ] 實作手機端與電腦端無縫雙向同步

## Task 15: 極簡走勢預測卡（20字原因）與每日歷史預測回測驗證勝率追蹤機制
- [x] 移除長篇大論文字，實作精簡「AI 走勢預測卡」（包含看漲/看跌方向、約 20 字精準核心理由、目標與防守價）
- [x] 實作「歷史預測回頭驗證引擎」：依據歷史 K 線每日指標模擬預測，並逐日比對次日實際漲跌，統計真實勝率（如 4勝1敗，勝率 80%）
- [x] 支援自選股專屬預測履歷：自選股卡片直接顯示預測標籤與勝率，並提供展開式「每日預測回測驗證紀錄」
- [x] 驗證前端互動與排版、執行單元測試並部署至 GitHub Pages

---

## 成果審查 (Review & Verification)
- [x] **單元測試全數通過**：執行 `python3 -m unittest discover -s tests -p "test_*.py"`，13 個測試案例 (指標計算、極值通道、TWSE 轉換、Mock 解析、資料庫 CRUD、回測引擎撮合與停損停利) 全部通過。
- [x] **Albedo 整合驗證通過**：執行 `verify_stock_service.py` 與 `run_backtest` 獨立測試，全數通過。
- [x] **CLI 功能驗證**：驗證 `main.py --help` 正確解析 `--dry-run`、`--once` 與 `--tickers` 參數。
- [x] **容器化與 NAS 準備**：已配置 Dockerfile 及 docker-compose.yml，包含 `./data:/app/data` 持久化磁碟映射與 `TZ=Asia/Taipei`。
- [x] **文件齊備**：已產出完整的使用手冊 `README.md`、開發者擴充指南 `DEVELOPER.md` 與整合文件 `albedo_integration.md`。

