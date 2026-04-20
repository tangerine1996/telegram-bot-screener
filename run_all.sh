#!/bin/bash
# Move to the project directory
cd "$(dirname "$0")"

echo "--- Execution started at $(date) ---"
/usr/bin/python3 finviz_screener.py && /usr/bin/python3 telegram_bot.py
echo "--- Execution finished at $(date) ---"
