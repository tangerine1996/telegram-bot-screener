import os
import requests
import pandas as pd
from datetime import datetime
from finvizfinance.quote import finvizfinance as Quote

def get_ticker_news(ticker_symbol):
    """Pobiera tylko newsy z Finviz dla danego tickera."""
    try:
        ticker = Quote(ticker_symbol)
        news_df = ticker.ticker_news()
        if news_df is not None and not news_df.empty:
            latest = news_df.iloc[0]
            return latest['Title'], latest['Link'], latest['Date']
    except Exception as e:
        print(f"Błąd pobierania newsów dla {ticker_symbol}: {e}")
    return None, None, None

def format_float(val):
    """Formatuje liczbę akcji (float) do formatu z Finviz (np. 15.0M)."""
    try:
        val = float(val)
        if val >= 1_000_000_000:
            return f"{val / 1_000_000_000:.1f}B"
        elif val >= 1_000_000:
            return f"{val / 1_000_000:.1f}M"
        elif val >= 1_000:
            return f"{val / 1_000:.1f}K"
        return str(val)
    except:
        return "N/A"

def get_tradingview_data():
    """Pobiera dane z TradingView API uwzględniając premarket."""
    URL = "https://scanner.tradingview.com/america/scan"
    
    payload = {
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",
            "close",
            "volume",
            "float_shares_outstanding",
            "relative_volume_10d_calc",
            "premarket_change"
        ],
        "filter": [
            {"left": "close", "operation": "greater", "right": 1},
            {"left": "close", "operation": "less", "right": 20},
            {"left": "float_shares_outstanding", "operation": "less", "right": 20000000},
            {"left": "relative_volume_10d_calc", "operation": "greater", "right": 3},
            {"left": "premarket_change", "operation": "greater", "right": 3}
        ],
        "range": [0, 50] # Top 50 wyników
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    try:
        print("Łączenie z TradingView...")
        r = requests.post(URL, json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
        
        if not data:
            return pd.DataFrame()

        rows = [x["d"] for x in data]
        df = pd.DataFrame(rows, columns=[
            'Ticker', 'Price', 'Volume', 'Float_Val_Raw', 'Rel_Vol', 'Premarket_Change'
        ])
        
        # Dostosowanie danych do formatu bota
        df['Change'] = df['Premarket_Change'] / 100 # Konwersja na ułamek (np. 5.5 -> 0.055)
        df['Gap_Val'] = df['Change'] # Bot używa Gap_Val w wiadomości
        df['Float_Val'] = df['Float_Val_Raw'].apply(format_float)
            
        return df
    except Exception as e:
        print(f"Błąd TradingView: {e}")
        return pd.DataFrame()

def run_screener():
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"--- TradingView + Finviz News Screener ({timestamp_str}) ---")
    
    results_dir = "results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    try:
        df = get_tradingview_data()
        
        if df.empty:
            print("Nie znaleziono spółek spełniających kryteria.")
            return

        print(f"Pobieranie newsów dla {len(df.head(10))} spółek z Finviz...")
        df = df.head(10).copy()
        
        titles, links, dates = [], [], []
        
        for ticker in df['Ticker']:
            print(f"  > {ticker}")
            title, link, date = get_ticker_news(ticker)
            titles.append(title)
            links.append(link)
            dates.append(date)
            
        df['News_Title'] = titles
        df['News_Link'] = links
        df['News_Date'] = dates
        
        # Uporządkowanie kolumn - usunięto zbędne N/A
        ordered_columns = [
            'Scan_Date', 'Ticker', 'Price', 'Change', 'Volume', 
            'News_Title', 'News_Link', 'News_Date', 'Float_Val', 'Rel_Vol', 'Gap_Val'
        ]
        
        # Wstawienie Scan_Date na początku
        df.insert(0, 'Scan_Date', timestamp_str)
        
        # Wybór i kolejność kolumn
        df = df[ordered_columns]
        
        # Ścieżka do zbiorczego pliku CSV
        output_file = os.path.join(results_dir, "screener_results_all.csv")
        
        # Zapis do CSV - dopisywanie (mode='a'), nagłówek tylko jeśli plik nie istnieje
        file_exists = os.path.isfile(output_file)
        df.to_csv(output_file, mode='a', index=False, header=not file_exists)
        print(f"Wyniki dopisane do: {output_file}")

    except Exception as e:
        print(f"Wystąpił błąd w run_screener: {e}")

if __name__ == "__main__":
    run_screener()
