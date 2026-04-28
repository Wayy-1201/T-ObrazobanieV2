#!/usr/bin/env bash
set -e

echo "▶ Запускаем Flask (app.py)..."
python app.py &

echo "▶ Запускаем Telegram-бот (bot.py)..."
python bot.py &

wait -n

echo "❌ Один из процессов завершился. Render перезапустит сервис."
exit 1
