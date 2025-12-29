#!/bin/bash

# Скрипт обновления приложения на VPS
# Использование: ./update_vps.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Параметры (можно изменить)
APP_USER=${APP_USER:-shopapp}
APP_DIR="/home/$APP_USER/app"

echo "=================================================="
echo "🔄 Обновление Telegram Shop"
echo "=================================================="

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    print_error "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Проверка существования директории
if [ ! -d "$APP_DIR" ]; then
    print_error "Директория приложения не найдена: $APP_DIR"
    exit 1
fi

cd $APP_DIR

# Создание резервной копии базы данных
print_step "Создание резервной копии базы данных..."
BACKUP_DIR="$APP_DIR/backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

# Получаем имя БД из .env
if [ -f "$APP_DIR/.env" ]; then
    source $APP_DIR/.env
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
    sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE
    print_step "Резервная копия создана: $BACKUP_FILE"
else
    print_warning "Файл .env не найден. Пропускаем резервное копирование БД."
fi

# Обновление кода (если используется git)
if [ -d "$APP_DIR/.git" ]; then
    print_step "Получение обновлений из Git..."
    sudo -u $APP_USER git pull
else
    print_warning "Git репозиторий не найден. Убедитесь, что вы вручную обновили файлы."
fi

# Обновление Node.js зависимостей
print_step "Обновление Node.js зависимостей..."
sudo -u $APP_USER bash <<EOF
cd $APP_DIR
npm install
EOF

# Сборка фронтенда
print_step "Сборка фронтенда..."
sudo -u $APP_USER bash <<EOF
cd $APP_DIR
npm run build
EOF

# Обновление Python зависимостей
print_step "Обновление Python зависимостей..."
sudo -u $APP_USER bash <<EOF
cd $APP_DIR
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# Настройка прав доступа для Nginx
print_step "Обновление прав доступа для Nginx..."
chmod 755 /home/$APP_USER
chmod 755 $APP_DIR

if [ -d "$APP_DIR/dist" ]; then
    chown -R $APP_USER:www-data $APP_DIR/dist
    chmod -R 755 $APP_DIR/dist
fi

if [ -d "$APP_DIR/config" ]; then
    chown -R $APP_USER:www-data $APP_DIR/config
    chmod -R 755 $APP_DIR/config
fi

# Перезапуск приложения
print_step "Перезапуск приложения..."
systemctl restart shop-app

# Ожидание запуска
sleep 3

# Проверка статуса
if systemctl is-active --quiet shop-app; then
    print_step "✅ Приложение успешно обновлено и перезапущено!"
    
    # Показать последние логи
    print_step "Последние логи приложения:"
    journalctl -u shop-app -n 20 --no-pager
else
    print_error "❌ Ошибка при перезапуске приложения!"
    print_error "Проверьте логи: journalctl -u shop-app -n 50"
    exit 1
fi

# Очистка старых резервных копий (оставляем последние 10)
print_step "Очистка старых резервных копий..."
cd $BACKUP_DIR
ls -t backup_*.sql | tail -n +11 | xargs -r rm
print_step "Оставлено последних резервных копий: $(ls -1 backup_*.sql 2>/dev/null | wc -l)"

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Обновление завершено успешно!${NC}"
echo "=================================================="
echo ""
