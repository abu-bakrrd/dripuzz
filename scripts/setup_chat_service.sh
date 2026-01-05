#!/bin/bash

# ============================================================================
# СКРИПТ НАСТРОЙКИ ЧАТ-СЕРВИСА (WEBSOCKETS)
# ============================================================================

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() { echo -e "${GREEN}[STEP]${NC} $1"; }
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    print_error "Запустите скрипт с правами root: sudo bash scripts/setup_chat_service.sh"
    exit 1
fi

# Параметры (подгружаем из .env если есть)
APP_DIR=$(pwd)
if [ ! -f "$APP_DIR/package.json" ]; then
    print_error "Скрипт должен запускаться из корневой директории приложения!"
    exit 1
fi

# Получаем пользователя приложения
APP_USER=$(ls -ld . | awk '{print $3}')
print_info "Пользователь приложения: $APP_USER"

# 1. Сборка сервера (если еще не собрано)
print_step "Сборка Node.js сервера..."
sudo -u $APP_USER npm run build

# 2. Создание systemd сервиса для чата
print_step "Создание systemd сервиса для чата..."
cat > /etc/systemd/system/shop-chat.service <<EOF
[Unit]
Description=Telegram Shop WebSocket Chat Service
After=network.target postgresql.service shop-app.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="NODE_ENV=production"
Environment="PORT=5002"
Environment="SKIP_FLASK=true"
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/node dist/index.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable shop-chat
systemctl restart shop-chat

# 3. Обновление конфигурации Nginx
print_step "Обновление конфигурации Nginx для поддержки WebSocket..."
NGINX_CONF="/etc/nginx/sites-available/shop"

if [ ! -f "$NGINX_CONF" ]; then
    print_error "Конфиденциальный файл Nginx '$NGINX_CONF' не найден!"
    exit 1
fi

# Добавляем location /ws если его еще нет
if ! grep -q "location /ws" "$NGINX_CONF"; then
    # Вставляем перед последней закрывающей скобкой серверного блока
    # Или лучше перед location /
    sed -i '/location \/ {/i \
    location /ws {\
        proxy_pass http://127.0.0.1:5002;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection "upgrade";\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
    }\
    ' "$NGINX_CONF"
    
    print_info "WebSocket location добавлен в Nginx"
else
    print_info "WebSocket location уже существует в Nginx, проверяем заголовки..."
    # Можно добавить логику обновления если нужно
fi

# Проверка и перезапуск Nginx
if nginx -t; then
    systemctl restart nginx
    print_step "✅ Чат-сервис успешно настроен и запущен!"
else
    print_error "Ошибка в конфигурации Nginx!"
    exit 1
fi

print_info "Статус сервиса чата:"
systemctl status shop-chat --no-pager
