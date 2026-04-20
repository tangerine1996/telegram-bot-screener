# 🚀 Stock Premarket Screener & Trading Suite

A modular Python-based ecosystem designed to identify, report, and archive high-momentum US stocks. It filters premarket data, delivers real-time Telegram alerts, and archives intraday 1-minute klines with visual charts for post-market analysis.

## 📊 Core Features

- **Premarket Scanning (TradingView API):** Precision data extraction from TradingView's live premarket feed.
- **Dynamic Technical Indicators:** Price, Premarket Gap (> +3%), High-Volume filtering (> 1M), and Relative Volume (Rel Vol) calculations.
- **Finviz News Integration:** Automatically fetches the latest news link and timestamp for every identified ticker.
- **Intraday Data Collector:** Downloads 1-minute historical data (Klines) for all screened stocks at the end of the trading day.
- **Automatic Chart Generation:** Generates professional PNG candlestick charts with session highlighting:
    - **Gray Background:** Premarket and After-hours.
    - **White Background:** Regular Trading Session.
- **Decoupled Architecture:** Separate scripts for scanning, messaging, and data archiving for maximum reliability.

## 🛠 Project Structure

- `finviz_screener.py`: The data engine. Fetches data from TradingView and news from Finviz.
- `telegram_bot.py`: The messenger. Sends formatted HTML reports based on the latest scan.
- `data_collector.py`: The archiver. Downloads 1m klines and generates PNG visual charts.
- `run_all.sh`: Helper script to execute the full morning pipeline (Scan -> Send).
- `results/`: Historical scan data (CSV).
- `results/klines/`: Intraday 1m data (CSV) and session charts (PNG).

## 📋 Setup & Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Ensure your `.env` file is set up with:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

3. **Modify Filters:**
   Edit `SCREENER_FILTERS` at the top of `finviz_screener.py` to adjust your trading criteria.

## ⚙️ Automation (System Cron)

The system is designed to be fully autonomous using system cron.

### 1. Morning Report (09:15 AM ET)
Triggers the scan and sends the Telegram report 15 minutes before the market opens.
```bash
CRON_TZ=America/New_York
15 9 * * 1-5 /home/serveradmin/projects/trading-screener/run_all.sh >> /home/serveradmin/projects/trading-screener/execution.log 2>&1
```

### 2. End-of-Day Archiving (23:00 Local Time)
Downloads full intraday 1m data and generates charts for all tickers scanned that morning.
```bash
0 23 * * 1-5 /usr/bin/python3 /home/serveradmin/projects/trading-screener/data_collector.py >> /home/serveradmin/projects/trading-screener/klines_execution.log 2>&1
```

## 📊 Manual Execution

- **Full Morning Pipeline:** `./run_all.sh`
- **Collect Intraday Data/Charts:** `python3 data_collector.py`

## ⚖️ License
This project is for personal trading research purposes. Use at your own risk.
