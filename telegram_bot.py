import os
import asyncio
import html
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from telegram import Bot
from telegram.constants import ParseMode

# Load configuration
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CSV_PATH = os.path.join("results", "screener_results_all.csv")

def format_number(val):
    """Formats large numbers into human-readable strings (e.g., 1.5M)."""
    try:
        val = float(val)
        if val >= 1_000_000_000: return f"{val / 1_000_000_000:.1f}B"
        if val >= 1_000_000: return f"{val / 1_000_000:.1f}M"
        if val >= 1_000: return f"{val / 1_000:.1f}K"
        return f"{val:.0f}"
    except: return "N/A"

def clean_html(text):
    """Escapes HTML special characters to prevent Telegram API errors."""
    if not isinstance(text, str): return ""
    return html.escape(text)

async def send_to_telegram():
    """Reads latest results from CSV and sends a formatted report to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] ERROR: Telegram configuration missing in .env")
        return

    if not os.path.exists(CSV_PATH):
        print(f"[!] ERROR: Data file {CSV_PATH} not found.")
        return

    try:
        full_df = pd.read_csv(CSV_PATH)
        if full_df.empty:
            print("[!] CSV file is empty.")
            return

        # Get rows from the latest scan session
        last_ts = full_df['Scan_Date'].max()
        df = full_df[full_df['Scan_Date'] == last_ts]

        message = f"🚀 <b>SCREENER REPORT</b>\n"
        message += f"<i>Generated at: {last_ts}</i>\n\n"

        for _, row in df.iterrows():
            ticker = clean_html(str(row['Ticker']))
            price = f"${row['Price']:.2f}"
            
            # Format performance data
            chg_pm = float(row.get('PM_Change', 0))
            gap_pm = float(row.get('PM_Gap', 0))
            chg_str = f"{'+' if chg_pm > 0 else ''}{chg_pm:.2f}%"
            gap_str = f"{gap_pm:+.2f}%"
            
            # Format technical data
            vol_pm = format_number(row.get('PM_Volume', 0))
            rel_vol = f"{row.get('Rel_Vol', 0):.2f}"
            float_shares = format_number(row.get('Float', 0))
            
            # News info
            news_link = str(row.get('News_Link', ''))
            news_date = clean_html(str(row.get('News_Date', '')))
            
            if news_link and news_link != "nan":
                news_info = f"📅 <a href='{news_link}'><b>Latest News</b></a>\n   <i>({news_date})</i>"
            else:
                news_info = "📅 No recent news found."

            # Construct HTML section for the ticker
            finviz_url = f"https://finviz.com/quote.ashx?t={ticker}"
            message += f"🔹 <b><a href='{finviz_url}'>{ticker}</a></b>\n"
            message += f"   💰 Price: <code>{price}</code> | PM: <b>{chg_str}</b>\n"
            message += f"   ⚡ Gap: <code>{gap_str}</code> | Rel Vol: <code>{rel_vol}</code>\n"
            message += f"   📊 PM Vol: <code>{vol_pm}</code> | Float: <code>{float_shares}</code>\n"
            message += f"   {news_info}\n\n"

        # Initialize bot and send message
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Report sent successfully.")

    except Exception as e:
        print(f"[!] Send error: {e}")

if __name__ == "__main__":
    asyncio.run(send_to_telegram())
