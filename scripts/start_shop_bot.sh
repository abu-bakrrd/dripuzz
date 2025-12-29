#!/bin/bash
# Скрипт запуска Telegram Shop Bot

echo "========================================"
echo "  Telegram Shop Bot"
echo "========================================"
echo ""

# Переход в корень проекта
cd "$(dirname "$0")/.."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "[!] Файл .env не найден!"
    exit 1
fi

python3 telegram_bot/telegrambot.py
