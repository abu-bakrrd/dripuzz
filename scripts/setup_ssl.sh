#!/bin/bash
cd "$(dirname "$0")/.."

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Установка SSL сертификата (Let's Encrypt) ===${NC}"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Запустите скрипт с правами root: sudo ./setup_ssl.sh${NC}"
    exit 1
fi

# Установить Certbot
echo "Установка Certbot..."
apt update -qq
apt install -y certbot python3-certbot-nginx > /dev/null 2>&1

echo ""

# Запросить домен
read -p "Введите ваш домен (например: myshop.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Ошибка: домен не указан${NC}"
    exit 1
fi

# Запросить email
read -p "Введите ваш email для уведомлений: " EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${RED}Ошибка: email не указан${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Проверка DNS...${NC}"

# Проверить, что домен резолвится
if ! host $DOMAIN > /dev/null 2>&1; then
    echo -e "${RED}⚠️  Домен $DOMAIN не резолвится!${NC}"
    echo ""
    echo "Возможные причины:"
    echo "1. DNS записи еще не обновились (подождите 15-30 минут)"
    echo "2. DNS записи настроены неправильно"
    echo ""
    echo "Проверьте DNS запись:"
    echo "  A-запись: $DOMAIN → ваш IP адрес"
    echo ""
    read -p "Продолжить установку SSL? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Установка отменена"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Получение SSL сертификата для: $DOMAIN и www.$DOMAIN${NC}"
echo "Это может занять 1-2 минуты..."
echo ""

# Получить сертификат
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ SSL сертификат успешно установлен!${NC}"
    echo ""
    echo "Теперь ваш сайт доступен по HTTPS:"
    echo -e "  ${BLUE}https://$DOMAIN${NC}"
    echo -e "  ${BLUE}https://www.$DOMAIN${NC}"
    echo ""
    echo -e "${GREEN}🔄 Сертификат будет автоматически обновляться${NC}"
    echo ""
    echo -e "${YELLOW}📱 Следующий шаг - обновите URL в Telegram BotFather:${NC}"
    echo "1. Откройте @BotFather в Telegram"
    echo "2. /mybots → Выберите бота → Bot Settings → Menu Button"
    echo "3. Введите новый URL: https://$DOMAIN"
    echo ""
else
    echo ""
    echo -e "${RED}❌ Ошибка при установке SSL${NC}"
    echo ""
    echo "Возможные причины:"
    echo "1. Домен не резолвится в ваш IP адрес"
    echo "2. Порты 80/443 закрыты в firewall"
    echo "3. Nginx не настроен правильно"
    echo ""
    echo "Проверьте:"
    echo "  ping $DOMAIN  # должен вернуть ваш IP"
    echo "  sudo ufw status  # проверить firewall"
    echo "  sudo nginx -t  # проверить конфигурацию"
    echo ""
    exit 1
fi
