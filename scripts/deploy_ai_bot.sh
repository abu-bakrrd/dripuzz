#!/bin/bash

# Скрипт для развертывания AI бота на VPS
# Этот скрипт запускает AI бота как systemd сервис

set -e

echo "🤖 Развертывание AI Customer Bot на VPS"
echo "========================================"

# Проверяем, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Пожалуйста, запустите скрипт с sudo"
    exit 1
fi

# Получаем путь к приложению
APP_DIR="/home/shopapp/app"
BOT_DIR="$APP_DIR/ai_bot"

echo ""
echo "📂 Путь к приложению: $APP_DIR"

# Проверяем существование папки
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Папка $APP_DIR не найдена!"
    echo "Сначала разверните основное приложение с помощью deploy_vps.sh"
    exit 1
fi

# Проверяем существование папки бота
if [ ! -d "$BOT_DIR" ]; then
    echo "❌ Папка $BOT_DIR не найдена!"
    exit 1
fi

echo ""
echo "📦 Установка зависимостей Python для AI бота..."
cd "$APP_DIR"
source venv/bin/activate
pip install google-generativeai pyTelegramBotAPI python-dotenv psycopg2-binary
deactivate

echo ""
echo "⚙️  Создание systemd сервиса для AI бота..."

# Создаем systemd unit file
cat > /etc/systemd/system/ai-bot.service << EOF
[Unit]
Description=AI Customer Support Bot
After=network.target postgresql.service shop-app.service

[Service]
Type=simple
User=shopapp
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
# Используем .env файл из корня приложения (так как там все ключи)
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python3 ai_bot/ai_customer_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd сервис ai-bot создан"

echo ""
echo "🔄 Перезагрузка systemd и запуск бота..."

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable ai-bot.service

# Запускаем бота
systemctl restart ai-bot.service

echo ""
echo "✅ AI Бот успешно развернут!"
echo ""
echo "📊 Полезные команды:"
echo "  Статус бота:     sudo systemctl status ai-bot"
echo "  Логи бота:       sudo journalctl -u ai-bot -f"
echo "  Перезапуск:      sudo systemctl restart ai-bot"
echo "  Остановка:       sudo systemctl stop ai-bot"
echo ""
echo "🔍 Проверяем статус..."
sleep 2
systemctl status ai-bot --no-pager
