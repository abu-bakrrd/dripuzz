#!/bin/bash

# Скрипт полного УДАЛЕНИЯ приложения с VPS
# Использование: ./uninstall_vps.sh

set -e

# Цвета
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}⚠️  ВНИМАНИЕ! ЭТОТ СКРИПТ УДАЛИТ ВЕСЬ ПРОЕКТ!${NC}"
echo "Будут удалены:"
echo "  1. Папка приложения /home/shopapp/app"
echo "  2. Сервисы systemd (shop-app, ai-bot, telegram-bot)"
echo "  3. Конфигурация Nginx"
echo ""

read -p "Вы уверены? Напишите 'DELETE' для подтверждения: " CONFIRM
if [ "$CONFIRM" != "DELETE" ]; then
    echo "Отмена."
    exit 0
fi

if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите с sudo"
    exit 1
fi

echo ""
echo "🛑 Остановка сервисов..."
systemctl stop shop-app || true
systemctl stop ai-bot || true
systemctl stop telegram-bot || true
systemctl disable shop-app || true
systemctl disable ai-bot || true
systemctl disable telegram-bot || true
echo "✅ Сервисы остановлены."

echo ""
echo "🗑 Удаление файлов..."
rm -rf /home/shopapp/app
rm -f /etc/systemd/system/shop-app.service
rm -f /etc/systemd/system/ai-bot.service
rm -f /etc/systemd/system/telegram-bot.service
systemctl daemon-reload
echo "✅ Файлы приложения удалены."

echo ""
echo "🌐 Удаление Nginx конфига..."
rm -f /etc/nginx/sites-enabled/shop
rm -f /etc/nginx/sites-available/shop
systemctl restart nginx
echo "✅ Nginx очищен."

echo ""
read -p "❓ Удалить базу данных 'shop_db'? (y/n): " DEL_DB
if [[ "$DEL_DB" == "y" || "$DEL_DB" == "Y" ]]; then
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS shop_db;"
    sudo -u postgres psql -c "DROP USER IF EXISTS shop_user;"
    echo "✅ База данных удалена."
else
    echo "База данных оставлена."
fi

echo ""
echo -e "${RED}❌ Проект MiniTaskerBot3 полностью удален с сервера.${NC}"
