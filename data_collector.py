import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import pytz

# ==============================================================================
# CONFIGURATION
# ==============================================================================
SCREENER_RESULTS_CSV = os.path.join("results", "screener_results_all.csv")
KLINES_DIR = os.path.join("results", "klines")
# ==============================================================================

def get_latest_tickers():
    """Reads the latest tickers from the screener results CSV."""
    if not os.path.exists(SCREENER_RESULTS_CSV):
        print(f"[!] Error: {SCREENER_RESULTS_CSV} not found.")
        return [], None

    try:
        df = pd.read_csv(SCREENER_RESULTS_CSV)
        if df.empty:
            return [], None

        # Identify the latest scan session date
        latest_ts = df['Scan_Date'].max()
        latest_date_str = latest_ts.split(' ')[0]
        
        tickers = df[df['Scan_Date'] == latest_ts]['Ticker'].unique().tolist()
        return tickers, latest_date_str
    except Exception as e:
        print(f"[!] Error reading CSV: {e}")
        return [], None

def download_intraday_data(ticker, date_str):
    """Downloads 1m intraday data for a specific ticker and date."""
    print(f"  > Downloading data for {ticker}...")
    
    try:
        # Define the date range (Current day from midnight to midnight to capture all sessions)
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = target_date.strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Download data with extended hours (premarket and after-hours)
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

        # Flatten multi-index columns if necessary (yfinance sometimes returns them)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Ensure index is datetime and localized to UTC, then convert to US/Eastern
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        data.index = data.index.tz_convert('America/New_York')

        # Filter data to keep only the target date in ET (just in case)
        data = data[data.index.strftime('%Y-%m-%d') == date_str]
        
        return data

    except Exception as e:
        print(f"    [!] Error downloading {ticker}: {e}")
        return None

def save_klines():
    """Main function to fetch and save intraday data for screened tickers."""
    print(f"--- INTRADAY DATA COLLECTOR START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    if not os.path.exists(KLINES_DIR):
        os.makedirs(KLINES_DIR)

    tickers, date_str = get_latest_tickers()
    if not tickers:
        print("[!] No tickers to process.")
        return

    print(f"Processing {len(tickers)} tickers for date: {date_str}")

    for ticker in tickers:
        filename = f"{ticker}_{date_str.replace('-', '_')}.csv"
        filepath = os.path.join(KLINES_DIR, filename)

        if os.path.exists(filepath):
            print(f"  [i] Data for {ticker} already exists. Skipping.")
            continue

        data = download_intraday_data(ticker, date_str)
        if data is not None:
            # Save to CSV (keeping index which contains the timestamp)
            data.to_csv(filepath)
            print(f"    [+] Saved to {filepath} ({len(data)} rows)")

if __name__ == "__main__":
    save_klines()
