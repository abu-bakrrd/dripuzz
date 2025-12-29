#!/bin/bash
# Скрипт запуска AI Customer Support Bot

echo "========================================"
echo "  AI Customer Support Bot"
echo "========================================"
echo ""

# Переход в директорию скрипта
cd "$(dirname "$0")"

# Проверка наличия .env файла в корне проекта
if [ ! -f ../.env ]; then
    echo "[!] Файл .env не найден в корне проекта!"
    echo ""
    echo "Создайте файл .env в корне проекта и добавьте:"
    echo "AI_BOT_TOKEN=ваш_токен_от_BotFather"
    echo "GEMINI_API_KEY=ваш_ключ_gemini"
    echo "DATABASE_URL=postgresql://user:password@localhost:5432/shop_db"
    echo ""
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 не найден!"
    echo "Установите Python 3"
    exit 1
fi

# Проверка зависимостей
echo "[1/2] Проверка зависимостей..."
if ! python3 -c "import google.generativeai" &> /dev/null; then
    echo ""
    echo "[!] Библиотека google-generativeai не установлена!"
    echo ""
    read -p "Установить сейчас? (y/n) " install_deps
    if [ "$install_deps" = "y" ] || [ "$install_deps" = "Y" ]; then
        echo ""
        echo "Установка зависимостей..."
        pip3 install google-generativeai pyTelegramBotAPI python-dotenv psycopg2-binary
        echo ""
    else
        echo ""
        echo "Установите зависимости вручную:"
        echo "pip3 install -r ../requirements.txt"
        echo ""
        exit 1
    fi
fi

echo "[2/2] Запуск AI бота..."
echo ""
echo "========================================"
echo "  Бот запускается..."
echo "========================================"
echo ""

python3 ai_customer_bot.py

if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo "  [!] Ошибка запуска бота"
    echo "========================================"
    echo ""
    exit 1
fi
