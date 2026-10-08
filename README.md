# StockChoice 股票自動化盤後監控與分析模組

StockChoice 是一個輕量、高效且模組化的盤後股票自動化篩選與監控工具，支援台股 (TWSE) 與美股 (yfinance / Yahoo Finance Chart API) 的歷史日 K 線獲取、純向量化技術指標計算、多條件複合策略篩選，並透過 Webhook (如 Discord) 推播警示。

---

## 快速開始 (本機環境)

### 1. 複製環境變數範本
```bash
cp .env.example .env
```
請編輯 `.env` 並填入您的 Discord Webhook URL：
```env
WEBHOOK_URL=https://discord.com/api/webhooks/your_id/your_token
NOTIFY_PLATFORM=discord
SCHEDULE_CRON_HOUR=15
SCHEDULE_CRON_MINUTE=0
```

### 2. 安裝 Python 套件依賴
```bash
pip install -r requirements.txt
```

### 3. 執行指令
- **空跑測試 (Dry Run，不發送真實 Webhook 推播)：**
  ```bash
  python src/main.py --dry-run
  ```
- **單次手動掃描 (指定股票代號)：**
  ```bash
  python src/main.py --once --tickers 2330.TW,AAPL,NVDA
  ```
- **常駐排程守護進程 (Daemon Mode，預設週一至週五 15:00 執行)：**
  ```bash
  python src/main.py
  ```

---

## NAS 部署教學 (Synology / QNAP / Docker 主機)

### 方式一：Docker Compose (推薦)
1. 將專案資料夾傳送至 NAS (例如 `/volume1/docker/stockchoice`)。
2. 於該資料夾建立並設定 `.env` 檔案。
3. 執行啟動指令：
   ```bash
   docker compose up -d --build
   ```
4. 查看運行狀態與紀錄：
   ```bash
   docker compose logs -f
   ```

### 方式二：Synology Container Manager (GUI 介面)
1. 在 Synology NAS 開啟 **Container Manager**。
2. 點選「專案」->「建立專案」。
3. 選擇放置 `docker-compose.yml` 與 `.env` 的本機目錄。
4. 點選「下一步」完成建置與背景運行。

---

## 資料持久化與備份
- 所有歷史日 K 線與警示紀錄均持久化於本地 SQLite 資料庫：`data/stock.db`。
- Docker 容器已映射 `./data:/app/data`，更新容器映像檔時資料庫不會遺失。

---

## 執行單元測試
```bash
python -m unittest discover -s tests -p "test_*.py"
```
