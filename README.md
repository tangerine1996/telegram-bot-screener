# 🚀 Stock Premarket Screener & Telegram Bot

A modular Python-based stock scanner that filters US stocks during the **Premarket** session and delivers formatted reports to Telegram. Optimized for professional execution using system `cron`.

## 📊 Core Features
- **Premarket Scanning (TradingView API):** Precision data extraction from TradingView's live premarket feed.
- **Dynamic Technical Indicators:**
  - **Price:** Live premarket price.
  - **Premarket Gap:** Filter for gaps > +3%.
  - **Premarket Volume:** High-volume filtering (> 1M).
  - **Relative Volume (Rel Vol):** Calculated as `PM Volume / Avg 30d Volume`.
  - **Float Shares:** Small-cap focus (< 20M shares).
- **Finviz News Integration:** Fetches the latest news link and timestamp for every identified ticker.
- **Decoupled Architecture:** Separate engine for data collection and messaging for maximum reliability.
- **CSV Archiving:** Appends all scan results to `results/screener_results_all.csv` for historical analysis.

## 🛠 Project Structure
- `finviz_screener.py`: The data engine. Fetches data from TradingView and news from Finviz.
- `telegram_bot.py`: The messenger. Reads the latest CSV entries and sends HTML reports.
- `run_all.sh`: A helper bash script to execute the full pipeline (Scan -> Send).
- `results/`: Directory containing the historical scan data in CSV format.
- `.env`: Secure storage for Telegram Bot Token and Chat ID.

## 📋 Setup & Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Create a `.env` file based on `.env.example`:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

3. **Adjust Filters:**
   You can easily modify scan criteria at the top of `finviz_screener.py`:
   ```python
   SCREENER_FILTERS = {
       "min_price": 1.0,
       "max_price": 20.0,
       "max_float": 20_000_000,
       "min_premarket_volume": 1_000_000,
       "min_premarket_gap": 3.0,
   }
   ```

## ⚙️ Automation (System Cron)

The project is designed to run via `cron`. It is recommended to schedule it 15 minutes before the US market opens (09:15 AM ET).

1. **Add to Crontab:**
   ```bash
   crontab -e
   ```

2. **Paste the following line** (adjust the path to your project directory):
   ```bash
   CRON_TZ=America/New_York
   15 9 * * 1-5 /home/user/trading-screener/run_all.sh >> /home/user/trading-screener/execution.log 2>&1
   ```

## 📊 Manual Execution
To run the full scan and send a report immediately:
```bash
./run_all.sh
```

## ⚖️ License
This project is for personal trading research purposes. Use at your own risk.
