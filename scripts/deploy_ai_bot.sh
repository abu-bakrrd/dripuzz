#!/bin/bash

# Скрипт для ОБНОВЛЕНИЯ или ОТДЕЛЬНОЙ установки AI бота (Mona)
# Использование: ./deploy_ai_bot.sh

set -e

echo "🤖 Обновление AI Customer Bot (Mona)..."
echo "========================================"

# Проверки
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите с sudo"
    exit 1
fi

APP_DIR="/home/shopapp/app"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Папка $APP_DIR не найдена!"
    echo "⚠️ Сначала выполните полную установку через ./deploy_vps.sh"
    exit 1
fi

echo "1. 📥 Получение обновлений кода..."
cd $APP_DIR
sudo -u shopapp git pull || echo "⚠️ Не удалось выполнить git pull (возможно, локальные изменения)"

echo "2. 🔧 Проверка конфигурации (.env)..."
if ! grep -q "AI_BOT_TOKEN" ".env"; then
    echo "⚠️ Токен бота не найден!"
    read -p "Введите Telegram TOKEN для AI Бота: " BOT_TOKEN
    read -p "Введите GROQ API KEY: " GROQ_KEY
    
    echo "" >> .env
    echo "# AI Bot Config" >> .env
    echo "AI_BOT_TOKEN=$BOT_TOKEN" >> .env
    echo "GROQ_API_KEY=$GROQ_KEY" >> .env
    chown shopapp:shopapp .env
    echo "✅ Конфигурация обновлена"
fi

echo "3. ⚙️ Настройка сервиса systemd..."
cat > /etc/systemd/system/ai-bot.service <<EOF
[Unit]
Description=AI Customer Support Bot
After=network.target postgresql.service shop-app.service

[Service]
Type=simple
User=shopapp
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python3 ai_bot/ai_customer_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-bot

echo "4. 🔄 Перезапуск AI бота..."
systemctl restart ai-bot

sleep 2
if systemctl is-active --quiet ai-bot; then
    echo "✅ AI Бот успешно обновлен и запущен!"
    echo "📜 Логи: sudo journalctl -u ai-bot -f"
else
    echo "❌ Ошибка запуска AI Бота."
    echo "🔍 Смотрите логи: journalctl -u ai-bot -n 20"
fi
