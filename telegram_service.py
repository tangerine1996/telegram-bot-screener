import os
import re
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

# Load configuration
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KLINES_DIR = os.path.join("results", "klines")
SCREENER_CSV = os.path.join("results", "screener_results_all.csv")

def get_available_dates():
    """Parses KLINES_DIR to find available years, months, and days."""
    data_tree = {}
    if not os.path.exists(KLINES_DIR):
        return data_tree

    # Filename pattern: TICKER_YYYY_MM_DD.png/csv
    pattern = re.compile(r"([A-Z]+)_(\d{4})_(\d{2})_(\d{2})\.(png|csv)")
    
    for filename in os.listdir(KLINES_DIR):
        match = pattern.match(filename)
        if match:
            ticker, year, month, day, ext = match.groups()
            
            if year not in data_tree:
                data_tree[year] = {}
            if month not in data_tree[year]:
                data_tree[year][month] = {}
            if day not in data_tree[year][month]:
                data_tree[year][month][day] = set()
            
            data_tree[year][month][day].add(ticker)
            
    return data_tree

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /data to browse the results archive.")

async def show_years(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data_tree = get_available_dates()
    if not data_tree:
        await update.message.reply_text("No data found in archive.")
        return

    years = sorted(data_tree.keys(), reverse=True)
    keyboard = [[InlineKeyboardButton(year, callback_data=f"year_{year}")] for year in years]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Select year:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    data_tree = get_available_dates()
    
    if data.startswith("year_"):
        year = data.split("_")[1]
        months = sorted(data_tree[year].keys())
        keyboard = []
        # Group months in rows of 3
        for i in range(0, len(months), 3):
            row = [InlineKeyboardButton(m, callback_data=f"month_{year}_{m}") for m in months[i:i+3]]
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_years")])
        await query.edit_message_text(f"Year {year}. Select month:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("month_"):
        _, year, month = data.split("_")
        days = sorted(data_tree[year][month].keys())
        keyboard = []
        # Group days in rows of 4
        for i in range(0, len(days), 4):
            row = [InlineKeyboardButton(d, callback_data=f"day_{year}_{month}_{d}") for d in days[i:i+4]]
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"year_{year}")])
        await query.edit_message_text(f"Year {year}, Month {month}. Select day:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("day_"):
        _, year, month, day = data.split("_")
        tickers = sorted(list(data_tree[year][month][day]))
        keyboard = []
        # Group tickers in rows of 3
        for i in range(0, len(tickers), 3):
            row = [InlineKeyboardButton(t, callback_data=f"ticker_{year}_{month}_{day}_{t}") for t in tickers[i:i+3]]
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"month_{year}_{month}")])
        await query.edit_message_text(f"Day {year}-{month}-{day}. Select ticker:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("ticker_"):
        _, year, month, day, ticker = data.split("_")
        date_str = f"{year}-{month}-{day}"
        
        # Load screener data
        info_text = f"📊 <b>Data for {ticker} on {date_str}</b>\n\n"
        try:
            df = pd.read_csv(SCREENER_CSV)
            # Filter by date (starts with year-month-day) and ticker
            ticker_data = df[(df['Scan_Date'].str.startswith(date_str)) & (df['Ticker'] == ticker)]
            
            if not ticker_data.empty:
                row = ticker_data.iloc[0]
                info_text += f"💰 Price: <code>${row['Price']:.2f}</code>\n"
                info_text += f"📈 PM Change: <code>{row['PM_Change']:.2f}%</code>\n"
                info_text += f"⚡ PM Gap: <code>{row['PM_Gap']:.2f}%</code>\n"
                info_text += f"📊 PM Vol: <code>{row['PM_Volume']:,.0f}</code>\n"
                info_text += f"🔄 Rel Vol: <code>{row['Rel_Vol']:.2f}</code>\n"
                info_text += f"💎 Float: <code>{row['Float']:,.0f}</code>\n"
                if str(row['News_Link']) != 'nan':
                    info_text += f"\n📰 <a href='{row['News_Link']}'>Latest News</a> ({row['News_Date']})"
            else:
                info_text += "⚠️ No detailed data found in CSV."
        except Exception as e:
            info_text += f"❌ Error reading CSV: {e}"

        # Path to image
        img_path = os.path.join(KLINES_DIR, f"{ticker}_{year}_{month}_{day}.png")
        
        if os.path.exists(img_path):
            with open(img_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=info_text,
                    parse_mode='HTML'
                )
        else:
            await query.message.reply_text(info_text + "\n\n⚠️ PNG chart not found.", parse_mode='HTML')

    elif data == "back_to_years":
        data_tree = get_available_dates()
        years = sorted(data_tree.keys(), reverse=True)
        keyboard = [[InlineKeyboardButton(year, callback_data=f"year_{year}")] for year in years]
        await query.edit_message_text("Select year:", reply_markup=InlineKeyboardMarkup(keyboard))

if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("data", show_years))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Service bot started...")
    app.run_polling()
