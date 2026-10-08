# StockChoice 開發總體規劃與實作指南 (Master Plan)

本文件專為後續接手開發的 AI 代理 (包含較低階模型) 與人類開發者設計，確保所有實作細節、架構設計與驗證標準在開發週期中維持一致。

## 1. 系統架構與開發環境
- **語言與執行環境**：Python 3.11+
- **套件管理**：使用 `requirements.txt` 以降低跨平台與容器化部署的環境配置複雜度。
- **專案目錄結構規範**：
  ```text
  stockchoice/
  ├── src/
  │   ├── main.py              # 主程式進入點與排程 (APScheduler) 註冊
  │   ├── data_ingestion/      # 資料爬取與清理 (TWSE API, yfinance)
  │   ├── ta_engine/           # 技術指標與矩陣運算 (Pandas)
  │   ├── scanner/             # 策略條件篩選邏輯
  │   ├── notifier/            # Webhook 推播模組
  │   └── database/            # SQLite CRUD 封裝與連線池
  ├── data/                    # 存放 SQLite 資料庫檔案與快取 (需 Git Ignore)
  ├── tests/                   # 測試案例 (Pytest)
  ├── docs/                    # 開發與使用手冊
  ├── .env.example             # 環境變數範例 (存放 Webhook 金鑰模板)
  ├── Dockerfile               # 容器化建置腳本
  └── docker-compose.yml       # NAS / Server 部署設定檔
  ```

## 2. 核心模組實作方式 (Implementation Details)
### 2.1 資料獲取模組 (Data Ingestion)
- **美股**：使用 `yfinance` 庫。呼叫 `yf.download(tickers, period="3mo")` 獲取日 K 線資料。
- **台股**：串接證交所 (TWSE) 開放資料 API (RESTful)。
  - 需實作防封鎖與 Retry 機制（建議使用 `tenacity` 套件），處理 API 請求超時與 HTTP 429 Too Many Requests 錯誤。
- **落地儲存**：取得資料後轉為 Pandas DataFrame，清洗空值後透過 `to_sql` 或 ORM 寫入 `data/stock.db` (SQLite)。

### 2.2 技術指標模組 (TA Engine)
- 統一透過 Pandas 的向量化運算 (Vectorization) 提升效能，避免使用 `for-loop` 迭代。
- **動態支撐與壓力位 (Rolling Extrema / Donchian Channels)**：
  - 壓力線：`df['upper_band'] = df['High'].rolling(window=20).max()`
  - 支撐線：`df['lower_band'] = df['Low'].rolling(window=20).min()`
- **移動平均 (MA)**：
  - 季線：`df['ma_60'] = df['Close'].rolling(window=60).mean()`

### 2.3 通知推播 (Notifier)
- 封裝 `requests.post()` 方法，傳送標準化 JSON Payload 至 Webhook。
- **資安規範**：嚴禁將 Webhook URL 寫死於程式碼中，必須從環境變數 (`os.getenv('WEBHOOK_URL')`) 讀取。

## 3. 版控方式 (Version Control Strategy)
- **初始化**：於專案根目錄執行 `git init`。
- **忽略清單 (.gitignore)**：必須排除 `.env` (避免機密外洩), `data/*.db` (避免二進位檔膨脹), `__pycache__/`, `.venv/`, `.pytest_cache/`。
- **Commit 規範**：採用 Conventional Commits 格式。
  - `feat: [模組名稱] 說明` (新增功能)
  - `fix: [模組名稱] 說明` (修復 Bug)
  - `docs: 說明` (文件更新)
  - `test: 說明` (測試相關)

## 4. NAS 部署策略 (NAS Deployment - Docker)
目標為在 Synology 等支援 Docker 的 NAS 設備上進行無頭 (Headless) 常駐運行。
- **映像檔建置 (Dockerfile)**：基於 `python:3.11-slim`，降低 Image Size。僅安裝必要系統依賴 (如 `build-essential`) 與 Python 套件。
- **持久化儲存 (Volume Mapping)**：在 `docker-compose.yml` 中配置 `./data:/app/data`，確保容器重啟或更新時，SQLite 內的股票代碼清單與歷史數據不會遺失。
- **時區對齊 (Timezone)**：配置環境變數 `TZ=Asia/Taipei`，確保 APScheduler 排程時間精準對齊台灣股市收盤時間 (如 14:30 或 15:00)。

## 5. 驗證與測試機制 (Testing & Validation)
為確保後續 AI 代理或開發者修改程式碼後不破壞既有邏輯，需遵循以下驗證標準：
- **單元測試 (Unit Tests)**：使用 `pytest`。針對 `ta_engine` 提供固定輸入的 Mock CSV 或 Mock DataFrame，斷言 (Assert) 算出的 MA 或區間極值精準符合預期數值。
- **Dry-run 模式 (空跑測試)**：在 `main.py` 提供 `--dry-run` 執行參數。啟用時，執行完整的資料抓取與指標計算，但**攔截真實的 Webhook 推播**，僅將警示訊息輸出至終端機 Log，供開發與驗證階段使用。

## 6. 開發與使用手冊撰寫計畫 (Documentation)
開發階段尾聲需產出以下兩份核心文件：
- **`README.md` (使用者手冊)**：指導最終用戶如何 Clone 專案、設定 `.env` 檔案中的 Webhook 金鑰，以及如何執行 `docker-compose up -d` 啟動服務。
- **`DEVELOPER.md` (開發者手冊)**：指導 AI Agent 或後續開發者如何擴充「新的選股策略」，包含應實作哪個 Interface、註冊邏輯以及如何撰寫對應的單元測試。
