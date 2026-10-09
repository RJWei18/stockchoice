# Albedo x StockChoice 整合部署與環境設定指南

本文件記錄將 `stockchoice` 整合為 Albedo 之 `StockAnalyst` 子智能體的環境設定、部署流程與獨立驗證方式。

---

## 一、環境設定與套件依賴

### 1. 套件依賴同步
Albedo 原有環境主要運行 Telegram Bot 與 Gemini SDK。串接 `stockchoice` 需要額外確保以下套件已列入 Albedo 根目錄之 `requirements.txt`：
```text
pandas>=2.0.0
yfinance>=0.2.30
tenacity>=8.2.3
```

### 2. 環境變數 (.env)
在 NAS 或本地的 Albedo `.env` 檔案中，確保具備以下設定（可直接使用現有 Albedo 金鑰）：
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
TZ=Asia/Taipei
```

---

## 二、NAS 部署流程

若 Albedo 已在 Synology NAS 以 Docker Compose 常駐運行：

### 步驟 1：同步程式碼至 NAS
在 NAS 專案目錄下執行 Git 更新：
```bash
cd /volume1/docker/albedo
git pull
```

### 步驟 2：重建並重啟容器
由於新增了 Python 依賴套件，需重新 Build 映像檔並重啟容器：
```bash
docker compose build albedo_bot
docker compose up -d albedo_bot
```

### 步驟 3：驗證運行狀態
檢視容器日誌確認 Bot 正常連線至 Telegram：
```bash
docker compose logs -f albedo_bot
```

---

## 三、獨立驗證機制 (Isolated Verification)

為避免直接修改生產環境之 `bot.py` 或線上 Telegram 服務，可先透過獨立適配層 `stock_service.py` 進行單元測試與功能驗證。

### 驗證目標
1. **單檔個股查詢 (`query_stock_status`)**：驗證給定股票代號 (如 `2330.TW` 或 `AAPL`) 能否正確透過數據模組取得最新價量、均線與支撐壓力位，並輸出格式化分析文字。
2. **策略掃描 (`run_scanner_filter`)**：驗證批次篩選能否正確計算指標並產出觸發報告。
3. **無損回退**：驗證過程完全在獨立測試腳本執行，不干擾 Telegram 線上運作。
