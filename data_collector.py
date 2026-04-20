import os
import pandas as pd
import yfinance as yf
import mplfinance as mpf
import matplotlib.pyplot as plt
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
            datetime_format='%H:%M'
        )

        ax = axes[0]
        
        # Highlight Extended Hours (Gray background)
        # We find the indices for the sessions
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

        data = data[data.index.strftime('%Y-%m-%d') == date_str]
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
        return

    print(f"Processing {len(tickers)} tickers for date: {date_str}")

    for ticker in tickers:
        base_name = f"{ticker}_{date_str.replace('-', '_')}"
        csv_path = os.path.join(KLINES_DIR, f"{base_name}.csv")
        png_path = os.path.join(KLINES_DIR, f"{base_name}.png")

        data = download_intraday_data(ticker, date_str)
        
        if data is not None:
            data.to_csv(csv_path)
            print(f"    [+] Saved CSV: {csv_path}")
            
            if generate_candlestick_chart(data, ticker, date_str, png_path):
                print(f"    [+] Generated Chart: {png_path}")

if __name__ == "__main__":
    save_klines_and_charts()
