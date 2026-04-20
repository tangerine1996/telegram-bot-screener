# 🚀 Stock Premarket Screener & Trading Suite

A modular Python-based ecosystem designed to identify, report, and archive high-momentum US stocks. It filters premarket data, delivers real-time Telegram alerts, and archives intraday 1-minute klines with visual charts for post-market analysis.

## 📊 Core Features

- **Premarket Scanning (TradingView API):** Precision data extraction from TradingView's live premarket feed.
- **Dynamic Technical Indicators:** Price, Premarket Gap (> +3%), High-Volume filtering (> 1M), and Relative Volume (Rel Vol) calculations.
- **Finviz News Integration:** Automatically fetches the latest news link and timestamp for every identified ticker.
- **Intraday Data Collector:** Downloads 1-minute historical data (Klines) for all screened stocks at the end of the trading day and sends a Telegram confirmation once complete.
- **Automatic Chart Generation:** Generates professional PNG candlestick charts with session highlighting.
- **Interactive Telegram Archive:** Browse historical data and charts directly via Telegram using an interactive menu.
- **Decoupled Architecture:** Separate scripts for scanning, messaging, and data archiving for maximum reliability.

## 🛠 Project Structure

- `finviz_screener.py`: The data engine. Fetches data from TradingView and news from Finviz.
- `telegram_bot.py`: The messenger. Sends automated morning reports via Cron.
- `telegram_service.py`: The interactive bot. Provides a UI to browse historical results and charts.
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

## ⚙️ Automation & Services

### 1. Interactive Bot Service (Systemd)
The interactive bot runs as a background service. To install it manually:

1. **Create the service file:**
   ```bash
   sudo nano /etc/systemd/system/stock_screener.service
   ```

2. **Paste the following configuration** (adjust `User` and `WorkingDirectory` if necessary):
   ```ini
   [Unit]
   Description=Stock Screener Telegram Interactive Bot
   After=network.target

   [Service]
   Type=simple
   User=serveradmin
   WorkingDirectory=/home/serveradmin/projects/trading-screener
   ExecStart=/usr/bin/python3 telegram_service.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable stock_screener.service
   sudo systemctl start stock_screener.service
   ```

- **Usage:** Send `/data` to the bot on Telegram to start browsing the archive.

### 2. Morning Report (Cron - 09:15 AM ET)
Triggers the scan and sends the Telegram report 15 minutes before the market opens.
```bash
CRON_TZ=America/New_York
15 9 * * 1-5 /home/serveradmin/projects/trading-screener/run_all.sh >> /home/serveradmin/projects/trading-screener/execution.log 2>&1
```

### 3. End-of-Day Archiving (Cron - 23:00 Local Time)
Downloads full intraday 1m data and generates charts for all tickers scanned that morning. Once finished, it sends a summary notification to Telegram.
```bash
0 23 * * 1-5 /usr/bin/python3 /home/serveradmin/projects/trading-screener/data_collector.py >> /home/serveradmin/projects/trading-screener/klines_execution.log 2>&1
```

## 📊 Manual Execution

- **Full Morning Pipeline:** `./run_all.sh`
- **Interactive Bot:** `python3 telegram_service.py`
- **Collect Intraday Data/Charts:** `python3 data_collector.py`

## ⚖️ License
This project is for personal trading research purposes. Use at your own risk.
