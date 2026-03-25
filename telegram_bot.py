import os
import time
import asyncio
import html
from datetime import datetime
import pytz
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode
import pandas as pd
from finviz_screener import run_screener

# Wczytywanie konfiguracji
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def format_volume(volume):
    try:
        volume = float(volume)
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.2f}K"
        return str(volume)
    except:
        return str(volume)

def clean_html(text):
    if not isinstance(text, str):
        return ""
    return html.escape(text)

async def send_to_telegram():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "TWÓJ_TOKEN_TUTAJ":
        print("BŁĄD: Uzupełnij TELEGRAM_BOT_TOKEN w pliku .env!")
        return

    # 1. Uruchomienie skanera (teraz on sam dopisuje do screener_results_all.csv)
    print(f"[{datetime.now()}] Uruchamiam skanowanie...")
    run_screener()

    # 2. Odczyt wyników
    results_dir = "results"
    csv_file = os.path.join(results_dir, "screener_results_all.csv")

    if not os.path.exists(csv_file):
        print("BŁĄD: Plik CSV nie został znaleziony.")
        return

    full_df = pd.read_csv(csv_file)
    if full_df.empty:
        print("Plik CSV jest pusty.")
        return

    # Pobieramy tylko wiersze z ostatniego skanowania (ostatni timestamp)
    last_timestamp = full_df['Scan_Date'].max()
    df = full_df[full_df['Scan_Date'] == last_timestamp]

    date_str = last_timestamp.split(' ')[0] # Tylko data do nagłówka

    if df.empty:
        message = f"ℹ️ <b>Finviz Screener</b>\n\nBrak nowych spółek na dzień {date_str}."
    else:
        # 2a. Obliczamy Rel Vol dla wszystkich i sortujemy
        df = df.copy()
        rel_vols_for_sort = []
        for _, row in df.iterrows():
            try:
                pm_vol_raw = float(row.get('Volume', 0))
                avg_vol_raw = float(row.get('Avg_Vol_30d_Raw', 0))
                rel_vols_for_sort.append(pm_vol_raw / avg_vol_raw if avg_vol_raw > 0 else 0)
            except:
                rel_vols_for_sort.append(0)
        
        df['Rel_Vol_Calc_Numeric'] = rel_vols_for_sort
        df = df.sort_values(by='Rel_Vol_Calc_Numeric', ascending=False)

        message = f"🚀 <b>TOP SPÓŁKI - FINVIZ ({date_str})</b>\n\n"

        for _, row in df.iterrows():
            ticker_symbol = clean_html(str(row['Ticker']))
            price = f"${row['Price']:.2f}"
            change_val = row['Change'] * 100
            change_str = f"{'+' if change_val > 0 else ''}{change_val:.2f}%"
            volume = format_volume(row['Volume'])
            
            # Nowe dane techniczne (Pobierane indywidualnie w finviz_screener.py)
            gap_val = row.get('Gap_Val', 'N/A')
            float_shares = row.get('Float_Val', 'N/A')
            
            # Pobieramy już wyliczony wcześniej Rel Vol
            rel_vol_numeric = row.get('Rel_Vol_Calc_Numeric', 0)
            rel_vol_calc = f"{rel_vol_numeric:.2f}" if rel_vol_numeric > 0 else "N/A"

            # Formatowanie Gap (zamiana ułamka na procent, jeśli to ułamek)
            try:
                if isinstance(gap_val, (float, int)):
                    gap_str = f"{gap_val*100:+.2f}%"
                else:
                    gap_str = str(gap_val)
            except:
                gap_str = str(gap_val)
            
            # Newsy - link i data
            news_date = clean_html(str(row.get('News_Date', '')))
            news_link = str(row.get('News_Link', ''))
            
            if news_date and news_date != "nan":
                # Finviz często zwraca relatywne linki, np. /news/123...
                if news_link.startswith('/'):
                    news_link = f"https://finviz.com{news_link}"
                
                news_info = f"📅 <a href='{news_link}'><i>Ostatni news: {news_date}</i></a>"
            else:
                news_info = "📅 Brak newsów."
            
            # Budowanie sekcji dla każdej spółki (HTML)
            finviz_url = f"https://finviz.com/quote.ashx?t={ticker_symbol}"
            message += f"🔹 <b><a href='{finviz_url}'>{ticker_symbol}</a></b>\n"
            message += f"   💰 Cena: <code>{price}</code> | <b>{change_str}</b>\n"
            message += f"   📊 PM Vol: <code>{volume}</code> | Rel Vol: <code>{rel_vol_calc}</code>\n"
            message += f"   📈 PM Gap: <code>{gap_str}</code> | Float: <code>{float_shares}</code>\n"
            message += f"   {news_info}\n\n"

    # 3. Wysyłka przez bota
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print("Pomyślnie wysłano zaktualizowany raport na Telegram.")
    except Exception as e:
        print(f"Błąd podczas wysyłania na Telegram: {e}")

def job():
    asyncio.run(send_to_telegram())

def run_scheduler():
    est = pytz.timezone('America/New_York')
    print("Bot wystartował. Harmonogram: 09:15 EST (Pn-Pt).")
    
    while True:
        now_est = datetime.now(est)
        # weekday() zwraca 0 dla Poniedziałku, ..., 4 dla Piątku
        if now_est.weekday() < 5:
            # Sprawdzenie godziny
            current_time_str = now_est.strftime("%H:%M")
            if current_time_str == "09:15":
                job()
                time.sleep(65) # Unikamy podwójnego wysłania w tej samej minucie
        
        time.sleep(30)

if __name__ == "__main__":
    run_scheduler()
