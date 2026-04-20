import os
import asyncio
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Bot
import pytz

# Load configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCREENER_RESULTS_CSV = os.path.join(BASE_DIR, "results", "screener_results_all.csv")
KLINES_DIR = os.path.join(BASE_DIR, "results", "klines")
# ==============================================================================

async def send_telegram_notification(date_str, tickers):
    """Sends a notification to Telegram with the list of processed tickers."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Telegram configuration missing. Skipping notification.")
        return

    if not tickers:
        print("[!] No tickers processed. Skipping notification.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    tickers_str = ", ".join(tickers)
    message = f"Today's ({date_str}) klines downloaded from stocks: {tickers_str}"
    
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print(f"[+] Telegram notification sent.")
    except Exception as e:
        print(f"[!] Error sending Telegram notification: {e}")

def get_latest_tickers():
    """Reads the latest tickers from the screener results CSV."""
    if not os.path.exists(SCREENER_RESULTS_CSV):
        print(f"[!] Error: {SCREENER_RESULTS_CSV} not found.")
        return [], None

    try:
        df = pd.read_csv(SCREENER_RESULTS_CSV)
        if df.empty:
            return [], None

        latest_ts = df['Scan_Date'].max()
        latest_date_str = latest_ts.split(' ')[0]
        
        tickers = df[df['Scan_Date'] == latest_ts]['Ticker'].unique().tolist()
        return tickers, latest_date_str
    except Exception as e:
        print(f"[!] Error reading CSV: {e}")
        return [], None

def generate_candlestick_chart(df, ticker, date_str, output_path):
    """Generates a candlestick chart with highlighted trading sessions using matplotlib integration."""
    try:
        # Define session break points
        # Regular Market Hours: 09:30 - 16:00 ET
        reg_start = pd.Timestamp(f"{date_str} 09:30:00").tz_localize('America/New_York')
        reg_end = pd.Timestamp(f"{date_str} 16:00:00").tz_localize('America/New_York')

        # Setup style
        mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')

        # Create plot
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=s,
            title=f"{ticker} - {date_str} (1m Klines)",
            ylabel='Price ($)',
            returnfig=True,
            tight_layout=True,
            datetime_format='%H:%M',
            warn_too_much_data=2000
        )

        ax = axes[0]

        # Force 30-minute ticks on x-axis, but only show labels on full hours
        tick_indices = []
        tick_labels = []
        for i, dt in enumerate(df.index):
            if dt.minute in [0, 30]:
                if dt.minute == 0:
                    label = dt.strftime('%H:%M')
                else:
                    label = "" # Empty string for 30-min ticks
                
                # Avoid duplicate labels if data is sparse
                if not tick_indices or (i - tick_indices[-1] > 10): 
                    tick_indices.append(i)
                    tick_labels.append(label)

        # Apply custom ticks (only if they fit reasonably)
        if tick_indices:
            ax.set_xticks(tick_indices)
            ax.set_xticklabels(tick_labels, rotation=0, fontsize=8)

        # Highlight Extended Hours (Gray background)
        # Regular Market Hours: 09:30 - 16:00 ET
        reg_start = pd.Timestamp(f"{date_str} 09:30:00").tz_localize('America/New_York')
        reg_end = pd.Timestamp(f"{date_str} 16:00:00").tz_localize('America/New_York')

        all_times = df.index
        
        # Premarket highlighting (anything before 09:30)
        pre_mask = all_times < reg_start
        if pre_mask.any():
            pre_indices = [i for i, x in enumerate(pre_mask) if x]
            ax.axvspan(pre_indices[0], pre_indices[-1], color='gray', alpha=0.15)
            
        # After-hours highlighting (anything after 16:00)
        post_mask = all_times > reg_end
        if post_mask.any():
            post_indices = [i for i, x in enumerate(post_mask) if x]
            ax.axvspan(post_indices[0], post_indices[-1], color='gray', alpha=0.15)

        # Save the figure
        plt.savefig(output_path)
        plt.close(fig)
        return True
    except Exception as e:
        print(f"    [!] Chart generation error for {ticker}: {e}")
        return False

def download_intraday_data(ticker, date_str):
    """Downloads 1m intraday data for a specific ticker and date."""
    print(f"  > Processing {ticker}...")
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = target_date.strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

        data = yf.download(
            tickers=ticker,
            start=start_date,
            end=end_date,
            interval="1m",
            prepost=True,
            progress=False
        )

        if data.empty:
            print(f"    [!] No data found for {ticker} on {date_str}.")
            return None

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert('America/New_York')

        # Filter by date and specific time range (04:00 - 16:00 ET)
        data = data[data.index.strftime('%Y-%m-%d') == date_str]
        data = data.between_time('04:00', '16:00')
        return data

    except Exception as e:
        print(f"    [!] Error downloading {ticker}: {e}")
        return None

def save_klines_and_charts():
    """Main function to fetch data and generate charts."""
    print(f"--- DATA COLLECTOR & CHART GENERATOR START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not os.path.exists(KLINES_DIR):
        os.makedirs(KLINES_DIR)

    tickers, date_str = get_latest_tickers()
    if not tickers:
        print("[!] No tickers to process.")
        return [], None

    print(f"Processing {len(tickers)} tickers for date: {date_str}")
    processed_tickers = []

    for ticker in tickers:
        base_name = f"{ticker}_{date_str.replace('-', '_')}"
        csv_path = os.path.join(KLINES_DIR, f"{base_name}.csv")
        png_path = os.path.join(KLINES_DIR, f"{base_name}.png")

        data = download_intraday_data(ticker, date_str)
        
        if data is not None:
            data.to_csv(csv_path)
            print(f"    [+] Saved CSV: {csv_path}")
            processed_tickers.append(ticker)
            
            if generate_candlestick_chart(data, ticker, date_str, png_path):
                print(f"    [+] Generated Chart: {png_path}")
    
    return processed_tickers, date_str

if __name__ == "__main__":
    processed, date_str = save_klines_and_charts()
    if processed and date_str:
        asyncio.run(send_telegram_notification(date_str, processed))
