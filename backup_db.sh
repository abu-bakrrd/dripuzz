#!/bin/bash

# Скрипт резервного копирования базы данных
# Использование: ./backup_db.sh

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Параметры
APP_USER=${APP_USER:-shopapp}
APP_DIR="/home/$APP_USER/app"
BACKUP_DIR="$APP_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Создание директории для резервных копий
mkdir -p $BACKUP_DIR

# Получение имени БД из .env
if [ -f "$APP_DIR/.env" ]; then
    source $APP_DIR/.env
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
else
    print_error "Файл .env не найден!"
    exit 1
fi

# Создание резервной копии
print_step "Создание резервной копии базы данных $DB_NAME..."
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"
sudo -u postgres pg_dump $DB_NAME > $BACKUP_FILE

# Сжатие резервной копии
print_step "Сжатие резервной копии..."
gzip $BACKUP_FILE

print_step "✅ Резервная копия создана: ${BACKUP_FILE}.gz"
print_step "Размер: $(du -h ${BACKUP_FILE}.gz | cut -f1)"

# Показать список всех резервных копий
echo ""
print_step "Все резервные копии:"
ls -lh $BACKUP_DIR/backup_*.sql.gz 2>/dev/null | awk '{print $9, $5}'

# Очистка старых резервных копий (оставляем последние 30)
print_step "Очистка старых резервных копий (оставляем последние 30)..."
cd $BACKUP_DIR
ls -t backup_*.sql.gz | tail -n +31 | xargs -r rm
print_step "Текущее количество резервных копий: $(ls -1 backup_*.sql.gz 2>/dev/null | wc -l)"

echo ""
print_step "Для восстановления используйте:"
echo "  gunzip -c ${BACKUP_FILE}.gz | sudo -u postgres psql $DB_NAME"
echo ""
