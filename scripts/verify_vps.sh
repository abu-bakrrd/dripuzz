#!/bin/bash
# Скрипт проверки состояния VPS для Monvoir Shop
# Использование: ./verify_vps.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "🔍 Проверка состояния VPS"
echo "========================================"

# 1. Проверка системных сервисов
echo -e "\n1. Проверка сервисов:"
SERVICE_NAME="shop-app"

if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Сервис $SERVICE_NAME работает${NC}"
else
    echo -e "${RED}❌ Сервис $SERVICE_NAME НЕ работает${NC}"
    echo "Статус:"
    systemctl status $SERVICE_NAME --no-pager | head -n 5
fi

if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✅ Nginx работает${NC}"
else
    echo -e "${RED}❌ Nginx НЕ работает${NC}"
fi

if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✅ PostgreSQL работает${NC}"
else
    echo -e "${RED}❌ PostgreSQL НЕ работает${NC}"
fi

# Боты
echo -e "\n1.1 Проверка ботов:"
if systemctl is-active --quiet ai-bot; then
    echo -e "${GREEN}✅ AI Bot работает${NC}"
else
    echo -e "${RED}❌ AI Bot НЕ работает${NC}"
fi

if systemctl is-active --quiet telegram-bot; then
    echo -e "${GREEN}✅ Shop Bot работает${NC}"
else
    echo -e "${RED}❌ Shop Bot НЕ работает${NC}"
fi

# 2. Проверка портов
echo -e "\n2. Проверка портов:"
if ss -tuln | grep -q ":5000"; then
    echo -e "${GREEN}✅ Порт 5000 (Flask) прослушивается${NC}"
else
    echo -e "${RED}❌ Порт 5000 НЕ прослушивается (Приложение не запущено?)${NC}"
fi

if ss -tuln | grep -q ":80"; then
    echo -e "${GREEN}✅ Порт 80 (HTTP) прослушивается${NC}"
else
    echo -e "${RED}❌ Порт 80 НЕ прослушивается${NC}"
fi

# 3. Проверка логов на ошибки
echo -e "\n3. Последние ошибки в логах (если есть):"
echo "--- Nginx Error Log ---"
tail -n 5 /var/log/nginx/shop_error.log 2>/dev/null || echo "Лог пуст или недоступен"

echo -e "\n--- App Service Log (последние 10 строк) ---"
journalctl -u $SERVICE_NAME -n 10 --no-pager

# 4. Проверка конфига
echo -e "\n4. Проверка конфигурации:"
APP_USER="shopapp"  # Предполагаемый юзер, можешь поменять если другой
APP_DIR="/home/$APP_USER/app"

if [ -f "$APP_DIR/.env" ]; then
    echo -e "${GREEN}✅ Файл .env найден${NC}"
    # Проверка наличия ключей (не показывая значения)
    if grep -q "DATABASE_URL" "$APP_DIR/.env"; then echo "  - DATABASE_URL: OK"; else echo -e "  - ${RED}DATABASE_URL: MISSING${NC}"; fi
    if grep -q "AI_BOT_TOKEN" "$APP_DIR/.env"; then echo "  - AI_BOT_TOKEN: OK"; else echo -e "  - ${YELLOW}AI_BOT_TOKEN: MISSING${NC}"; fi
    if grep -q "TELEGRAM_BOT_TOKEN" "$APP_DIR/.env"; then echo "  - TELEGRAM_BOT_TOKEN: OK"; else echo -e "  - ${YELLOW}TELEGRAM_BOT_TOKEN: MISSING${NC}"; fi
    if grep -q "GROQ_API_KEY" "$APP_DIR/.env"; then echo "  - GROQ_API_KEY: OK"; else echo -e "  - ${YELLOW}GROQ_API_KEY: MISSING${NC}"; fi
else
    echo -e "${RED}❌ Файл .env не найден в $APP_DIR${NC}"
fi

echo -e "\n========================================"
echo "🏁 Проверка завершена"
