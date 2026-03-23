# 🚀 Stock Premarket Screener & Telegram Bot

Automatyczny skaner giełdowy (Python), który filtruje spółki w trakcie sesji przedrynkowej (**Premarket**) i wysyła raporty na Telegram w dni handlowe o **09:00** i **09:15 EST** (pół godziny przed otwarciem giełdy w USA).

## 📊 Główne funkcje
- **Skanowanie Premarketu (TradingView API):** Bot pobiera precyzyjne dane bezpośrednio z TradingView, uwzględniając ruchy cenowe przed sesją główną.
- **Wyrafinowane Filtry:**
  - Cena: $1 - $20
  - Premarket Change: > 3%
  - Relative Volume (10d): > 3
  - Float Shares: < 20M
- **Raporty Telegram (HTML):**
  - Klikalne tickery (link do profilu na Finviz).
  - Dane techniczne: Cena, % Zmiany Premarket, Wolumen, Relative Volume, Gap %, Float.
  - **Bezpośrednie linki do newsów:** Kliknięcie w datę newsa przenosi prosto do artykułu na Finviz.
- **Niezawodność:** Bot działa jako usługa Linux `systemd` z automatycznym restartem i startem przy uruchomieniu systemu.
- **Archiwizacja danych:** Zapisuje ostatni skan do pliku `results/screener_results_all.csv` (tylko najświeższe wyniki).

## 🛠 Struktura Projektu
- `finviz_screener.py`: Silnik pobierający dane z TradingView i newsy z Finviz.
- `telegram_bot.py`: Harmonogram (09:00 i 09:15 EST) i wysyłka powiadomień.
- `.env`: Bezpieczne przechowywanie Tokena bota i ID czatu.
- `results/`: Katalog z wynikami skanowania w formacie CSV.

## 📋 Instalacja i Konfiguracja

1. **Zainstaluj zależności:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Skonfiguruj Środowisko:**
   Skopiuj `.env.example` do `.env` i uzupełnij swoje dane:
   ```env
   TELEGRAM_BOT_TOKEN=twój_token_tutaj
   TELEGRAM_CHAT_ID=twój_chat_id_tutaj
   ```

3. **Inicjalizacja Bota:**
   Znajdź swojego bota na Telegramie i kliknij **/start**.

## ⚙️ Zarządzanie Usługą

Bot działa jako usługa systemowa `screener-bot.service`.

- **Sprawdź status:**
  ```bash
  sudo systemctl status screener-bot.service
  ```

- **Logi na żywo:**
  ```bash
  journalctl -u screener-bot.service -f
  ```

- **Restart bota (po zmianach w kodzie):**
  ```bash
  sudo systemctl restart screener-bot.service
  ```

## 📊 Ręczne Uruchomienie
Aby wykonać skanowanie i wysłać raport natychmiast:
```bash
python3 -c "import asyncio; from telegram_bot import send_to_telegram; asyncio.run(send_to_telegram())"
```

## ⚖️ License
This project is for personal trading research purposes. Use at your own risk.
