# 🚀 Stock Premarket Screener & Telegram Bot

Automatyczny skaner giełdowy (Python), który filtruje spółki w trakcie sesji przedrynkowej (**Premarket**) i wysyła raporty na Telegram w dni handlowe o **09:15 EST** (15 minut przed otwarciem giełdy w USA).

## 📊 Główne funkcje
- **Skanowanie Premarketu (TradingView API):** Bot pobiera precyzyjne dane bezpośrednio z TradingView, korzystając z kolumny `premarket_close` (notowania na żywo przed sesją główną).
- **Wyrafinowane Filtry:**
  - Cena (Premarket): $1 - $20
  - Premarket Gap: < -3% lub > +3%
  - Premarket Volume: > 1,000,000
  - Float Shares: < 20M
- **Inteligentne Raporty Telegram (HTML):**
  - **Sortowanie:** Spółki są automatycznie sortowane od najwyższego do najniższego **Relative Volume** (wyliczanego dynamicznie: PM Vol / Avg 30d).
  - Klikalne tickery (link do profilu na Finviz).
  - **Dane techniczne:** Cena, % Zmiany PM, PM Vol, Rel Vol, PM Gap, Float.
  - **Bezpośrednie linki do newsów:** Kliknięcie w datę newsa przenosi prosto do artykułu na Finviz.
- **Niezawodność:** Bot działa jako usługa Linux `systemd` z automatycznym restartem i startem przy uruchomieniu systemu.
- **Archiwizacja danych:** Zapisuje każde skanowanie do pliku `results/screener_results_all.csv`, gromadząc historię skanowań (mode: append).

## 🛠 Struktura Projektu
- `finviz_screener.py`: Silnik pobierający dane z TradingView i newsy z Finviz.
- `telegram_bot.py`: Harmonogram (09:15 EST) i wysyłka powiadomień.
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

## ⚙️ Zarządzanie Usługą (Linux Systemd)

Aby bot działał w tle i uruchamiał się automatycznie po starcie systemu, najlepiej skonfigurować go jako usługę `systemd`.

1. **Stwórz plik usługi:**
   ```bash
   sudo nano /etc/systemd/system/screener-bot.service
   ```

2. **Wklej poniższą zawartość** (dostosuj ścieżki `/home/user/...` do swojej lokalizacji):
   ```ini
   [Unit]
   Description=Stock Premarket Screener Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=twoja_nazwa_uzytkownika
   WorkingDirectory=/home/twoja_nazwa_uzytkownika/trading-screener
   ExecStart=/usr/bin/python3 /home/twoja_nazwa_uzytkownika/trading-screener/telegram_bot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Aktywuj usługę:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable screener-bot.service
   sudo systemctl start screener-bot.service
   ```

- **Sprawdź status:** `sudo systemctl status screener-bot.service`
- **Logi na żywo:** `journalctl -u screener-bot.service -f`

## 🪟 Instrukcja dla Windows

1. **Instalacja:**
   - Zainstaluj Python ze strony [python.org](https://www.python.org/).
   - Pobierz kod bota i zainstaluj biblioteki: `pip install -r requirements.txt`.
   - Skonfiguruj plik `.env` (pamiętaj, aby nie używać cudzysłowu w wartościach, np. `TELEGRAM_BOT_TOKEN=123:ABC`).

2. **Uruchamianie w tle:**
   - Możesz po prostu zostawić otwarte okno terminala z komendą `python telegram_bot.py`.
   - **Harmonogram zadań (Task Scheduler):** Aby bot startował z systemem, dodaj nowe zadanie w "Harmonogramie zadań" Windows, wskazując `python.exe` jako program i ścieżkę do `telegram_bot.py` jako argument.

## 📊 Ręczne Uruchomienie (Test)
 Aby wykonać skanowanie i wysłać raport natychmiast:
 ```bash
 python3 -c "import asyncio; from telegram_bot import send_to_telegram; asyncio.run(send_to_telegram())"
 ```

## ⚖️ License
This project is for personal trading research purposes. Use at your own risk.
