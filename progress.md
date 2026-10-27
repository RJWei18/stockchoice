# StockChoice 開發進度

- 2026-10-08: 完成專案初始化配置，建立 `tasks/todo.md` 與 `design_spec.md`，確認階段一至階段四之開發計畫。
- 2026-10-09: 完成 Task 1 專案基礎環境建置 (git init, .gitignore, requirements.txt, 模組目錄結構, .env.example)。
- 2026-10-09: 完成 Task 2 至 Task 6 全功能開發與單元測試 (SQLite 儲存、TWSE/Yahoo 數據獲取、技術指標運算、多條件策略掃描、Webhook 推播、APScheduler 排程、Docker/NAS 部署設定檔與使用/開發者雙手冊)。單元測試全數通過。
- 2026-10-09: 完成 Task 7 與 Task 8：上線 GitHub Pages 前端儀表板、TradingView K線圖表時間軸與游標資訊優化、MACD (DIF/DEA/OSC) 擺盪指標圖、三大法人籌碼面動態分析面板與 GitHub Actions 自動化部署流程。
- 2026-10-17: 完成 Task 18：實作「歷史盲測挑戰實驗室 (Historical Blind Test Lab)」。包含去識別化標的隨機抽取切片、相對時間序軸遮蔽、逐回合 K 線即時步進、下單假說與理由筆記紀錄器、真身大揭曉、全景走勢解鎖與四象限決策覆盤分析機制。相容 Vercel、Supabase 與 GitHub Pages。
- 2026-10-27: 完成 Task 19 與 Task 20：
  1. 美股盤前與盤後速報：產出四大指數期貨/ETF、科技風向球、美股收盤總結與板塊輪動。
  2. 自選搜尋遮蔽 Bug 修復：分類切換自動清空搜尋框，並提供提示橫幅與一鍵清空按鈕。
  3. 訊號勝負判定與回測生命週期追蹤引擎 (Signal Outcome Evaluation Engine)：Pure function 判定模組 `src/backtest/signal_evaluator.py`，支援 BULLISH、BEARISH、NEUTRAL 與雙邊穿價保守判定機制，完成 9 項新單元測試（全套 22 項測試通過），前後端勝率指標與歷史履歷展示全面升級。
