# StockChoice 系統設計規格書

## 核心目標
股票自動化監控與技術分析工具，初期專注於盤後資料的策略選股。

## 系統架構
- 語言：Python 3.11+
- 資料處理：Pandas, NumPy, pandas-ta
- 資料儲存：SQLite
- 排程：APScheduler / Cronjob (盤後執行)
- 部署：Docker 容器化

## 核心決策紀錄
1. **資料源**：初期實作盤後選股。台股使用證交所開放資料，美股使用 `yfinance`。
2. **支撐與壓力位**：採用「區間極值 (Rolling Max/Min)」與長天期 MA 實作。
3. **推播頻率**：由於初期為盤後批次作業，每日僅觸發一次，無須實作複雜的狀態冷卻與防頻繁推播機制。
4. **歷史盲測挑戰實驗室 (Blind Backtest)**：
   - 定位：交易心理與決策直覺飛行模擬器，杜絕後見之明偏差。
   - 機制：去識別化隨機抽取歷史標的與區間切片，以相對時間軸 (Day 1..T) 遮蔽真實日期，提供前 30 根 K 棒作為觀察期。
   - 決策與覆盤：逐日推進時記錄下單理由（Thesis），結算後揭曉標的真身，比對實戰總報酬 vs. 同期 Buy & Hold，並針對每筆決策執行四象限偏差歸因。
   - 架構：純前端狀態機搭配 LocalStorage 本地儲存與 Supabase 非同步備份，相容於 Vercel 與 GitHub Pages。
5. **訊號勝負判定與回測生命週期引擎 (Signal Outcome Evaluation Engine)**：
   - 定位：客觀自動化判定系統給出之預測訊號勝負結果 (WIN / LOSS / PENDING)。
   - 狀態轉移規則：
     - 多頭 (BULLISH)：優先觸及停利價 -> WIN；優先觸及停損價 -> LOSS；滿 90 天 (63 交易日) 未碰 -> LOSS (逾時)；日內雙邊穿價保守判定為 LOSS；未達且未逾時 -> PENDING。
     - 空頭 (BEARISH)：優先觸及下檔停利 -> WIN；反彈觸及停損 -> LOSS；滿 90 天未碰 -> LOSS。
     - 平盤 (NEUTRAL)：突破基準價 $\pm 10\%$ 區間 -> LOSS；滿 90 天皆留在 $\pm 10\%$ 內 -> WIN；未滿 90 天 -> PENDING。
   - 勝率指標區隔：實戰交易勝率 (BULLISH/BEARISH) 與區間平盤命中率 (NEUTRAL) 獨立呈現，避免觀望訊號稀釋勝率。
6. **美股盤前盤後市場速報**：
   - 盤前速報 (`us_premarket_briefing`)：美股四大指數 ETF、Mag 7 科技風向球、美債 10 年期殖利率與 VIX 恐慌指數、盤前到價盯盤清單。
   - 盤後總結 (`us_postmarket_summary`)：終場主要指數漲跌、強弱勢板塊與 13F 機構資金動態。

