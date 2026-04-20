import os
import requests
import pandas as pd
from datetime import datetime
from finvizfinance.quote import finvizfinance as Quote

# ==============================================================================
# SCREENER FILTERS (Configuration)
# ==============================================================================
SCREENER_FILTERS = {
    "min_price": 1.0,
    "max_price": 20.0,
    "max_float": 20_000_000,
    "min_premarket_volume": 1_000_000,
    "min_premarket_gap": 3.0,  # Only positive gaps above +3%
}

# General settings
MAX_TICKERS_FOR_NEWS = 10
RESULTS_DIR = "results"
CSV_FILENAME = "screener_results_all.csv"
# ==============================================================================

TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

def fetch_tv_data():
    """Fetches stock data from TradingView API based on defined filters."""
    payload = {
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",
            "premarket_close",
            "premarket_change",
            "premarket_gap",
            "average_volume_30d_calc",
            "float_shares_outstanding",
            "premarket_volume"
        ],
        "filter": [
            {"left": "premarket_close", "operation": "greater", "right": SCREENER_FILTERS["min_price"]},
            {"left": "premarket_close", "operation": "less", "right": SCREENER_FILTERS["max_price"]},
            {"left": "float_shares_outstanding", "operation": "less", "right": SCREENER_FILTERS["max_float"]},
            {"left": "premarket_volume", "operation": "greater", "right": SCREENER_FILTERS["min_premarket_volume"]},
            {"left": "premarket_gap", "operation": "greater", "right": SCREENER_FILTERS["min_premarket_gap"]}
        ],
        "range": [0, 50],
        "sort": {"sortBy": "premarket_volume", "sortOrder": "desc"}
    }

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching data from TradingView...")
        r = requests.post(TRADINGVIEW_URL, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
        
        if not data:
            print("  [!] No stocks found matching criteria.")
            return pd.DataFrame()

        rows = [x["d"] for x in data]
        df = pd.DataFrame(rows, columns=[
            'Ticker', 'Price', 'PM_Change', 'PM_Gap', 'Avg_Vol_30d', 'Float', 'PM_Volume'
        ])
        return df
    except Exception as e:
        print(f"  [!] TradingView API Error: {e}")
        return pd.DataFrame()

def get_finviz_news_info(ticker_symbol):
    """Fetches the latest news link and timestamp from Finviz."""
    try:
        ticker = Quote(ticker_symbol)
        news_df = ticker.ticker_news()
        if news_df is not None and not news_df.empty:
            latest = news_df.iloc[0]
            link = latest['Link']
            if link.startswith('/'): link = f"https://finviz.com{link}"
            return link, latest['Date']
    except Exception as e:
        print(f"  [!] News fetch error for {ticker_symbol}: {e}")
    return None, None

def run_screener():
    """Main execution function for the data engine."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"--- SCREENER ENGINE START: {timestamp} ---")
    
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    
    df = fetch_tv_data()
    if df.empty:
        return

    # Calculate Relative Volume (PM Vol / Avg 30d Vol)
    df['Rel_Vol'] = df.apply(
        lambda x: x['PM_Volume'] / x['Avg_Vol_30d'] if x['Avg_Vol_30d'] > 0 else 0, 
        axis=1
    )

    # Limit results and fetch news
    df = df.head(MAX_TICKERS_FOR_NEWS).copy()
    print(f"Fetching news for {len(df)} tickers...")
    
    news_links, news_dates = [], []
    for ticker in df['Ticker']:
        print(f"  > Processing: {ticker}")
        link, date = get_finviz_news_info(ticker)
        news_links.append(link)
        news_dates.append(date)
        
    df['News_Date'] = news_dates
    df['News_Link'] = news_links
    df.insert(0, 'Scan_Date', timestamp)
    
    # Define column order (News_Link at the end for visual clarity)
    cols_order = [
        'Scan_Date', 'Ticker', 'Price', 'PM_Change', 'PM_Gap', 
        'Avg_Vol_30d', 'Float', 'PM_Volume', 'Rel_Vol', 
        'News_Date', 'News_Link'
    ]
    df = df[cols_order]
    
    # Save results to CSV (append mode)
    output_path = os.path.join(RESULTS_DIR, CSV_FILENAME)
    file_exists = os.path.isfile(output_path)
    df.to_csv(output_path, mode='a', index=False, header=not file_exists)
    print(f"Data saved successfully to: {output_path}")

if __name__ == "__main__":
    run_screener()
