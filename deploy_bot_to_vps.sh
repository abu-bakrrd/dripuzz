#!/bin/bash

# Скрипт для развертывания Telegram бота на VPS
# Этот скрипт запускает бота как systemd сервис на VPS

set -e

echo "🤖 Развертывание Telegram бота на VPS"
echo "======================================"

# Проверяем, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Пожалуйста, запустите скрипт с sudo"
    exit 1
fi

# Получаем путь к приложению
APP_DIR="/opt/telegram-shop"
BOT_DIR="$APP_DIR/telegram_bot"

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
echo "📦 Установка зависимостей Python для бота..."
cd "$BOT_DIR"

# Устанавливаем зависимости
pip3 install -r requirements.txt

echo ""
echo "🔧 Настройка .env файла для бота..."

# Проверяем существование .env файла
if [ ! -f "$BOT_DIR/.env" ]; then
    echo "⚠️  Файл .env не найден. Создаем новый..."
    
    # Запрашиваем данные
    read -p "Введите TELEGRAM_BOT_TOKEN: " BOT_TOKEN
    read -p "Введите CLOUDINARY_CLOUD_NAME: " CLOUD_NAME
    read -p "Введите CLOUDINARY_API_KEY: " API_KEY
    read -p "Введите CLOUDINARY_API_SECRET: " API_SECRET
    
    # Получаем DATABASE_URL из основного .env
    if [ -f "$APP_DIR/.env" ]; then
        DB_URL=$(grep DATABASE_URL "$APP_DIR/.env" | cut -d '=' -f2)
        # Заменяем IP на localhost для локального подключения
        DB_URL_LOCAL=$(echo $DB_URL | sed 's/@[0-9.]*:/@localhost:/')
    else
        echo "❌ Файл $APP_DIR/.env не найден!"
        exit 1
    fi
    
    # Создаем .env
    cat > "$BOT_DIR/.env" << EOF
DATABASE_URL=$DB_URL_LOCAL
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
CLOUDINARY_CLOUD_NAME=$CLOUD_NAME
CLOUDINARY_API_KEY=$API_KEY
CLOUDINARY_API_SECRET=$API_SECRET
EOF
    
    echo "✅ Файл .env создан"
else
    echo "✅ Файл .env уже существует"
    
    # Проверяем и обновляем DATABASE_URL на localhost
    if grep -q "DATABASE_URL=postgresql://.*@[0-9.]" "$BOT_DIR/.env"; then
        echo "🔄 Обновляем DATABASE_URL на localhost..."
        sed -i 's/@[0-9.]*:/@localhost:/g' "$BOT_DIR/.env"
        echo "✅ DATABASE_URL обновлен"
    fi
fi

echo ""
echo "⚙️  Создание systemd сервиса для бота..."

# Создаем systemd unit file
cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Shop Bot
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd сервис создан"

echo ""
echo "🔄 Перезагрузка systemd и запуск бота..."

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable telegram-bot.service

# Запускаем бота
systemctl restart telegram-bot.service

echo ""
echo "✅ Бот успешно развернут!"
echo ""
echo "📊 Полезные команды:"
echo "  Статус бота:     sudo systemctl status telegram-bot"
echo "  Логи бота:       sudo journalctl -u telegram-bot -f"
echo "  Перезапуск:      sudo systemctl restart telegram-bot"
echo "  Остановка:       sudo systemctl stop telegram-bot"
echo "  Запуск:          sudo systemctl start telegram-bot"
echo ""
echo "🔍 Проверяем статус..."
sleep 2
systemctl status telegram-bot --no-pager

echo ""
echo "🎉 Готово! Бот запущен на VPS."
