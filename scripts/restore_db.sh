#!/bin/bash

# Скрипт восстановления базы данных из резервной копии
# Использование: ./restore_db.sh [путь_к_резервной_копии]

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}[RESTORE]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Параметры
APP_USER=${APP_USER:-shopapp}
APP_DIR="/home/$APP_USER/app"
BACKUP_DIR="$APP_DIR/backups"

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    print_error "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Получение имени БД из .env
if [ -f "$APP_DIR/.env" ]; then
    source $APP_DIR/.env
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
else
    print_error "Файл .env не найден!"
    exit 1
fi

# Если путь к резервной копии не указан, показываем список
if [ -z "$1" ]; then
    print_step "Доступные резервные копии:"
    echo ""
    ls -lht $BACKUP_DIR/backup_*.sql.gz 2>/dev/null | nl | awk '{print $1") "$10, "("$6")"}'
    echo ""
    read -p "Введите номер резервной копии для восстановления (или путь к файлу): " BACKUP_CHOICE
    
    if [[ $BACKUP_CHOICE =~ ^[0-9]+$ ]]; then
        BACKUP_FILE=$(ls -t $BACKUP_DIR/backup_*.sql.gz | sed -n "${BACKUP_CHOICE}p")
    else
        BACKUP_FILE=$BACKUP_CHOICE
    fi
else
    BACKUP_FILE=$1
fi

# Проверка существования файла
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Файл резервной копии не найден: $BACKUP_FILE"
    exit 1
fi

print_warning "⚠️  ВНИМАНИЕ! Это действие ПЕРЕЗАПИШЕТ текущую базу данных: $DB_NAME"
print_warning "Все текущие данные будут удалены!"
echo ""
read -p "Вы уверены? Введите 'yes' для продолжения: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_step "Восстановление отменено"
    exit 0
fi

# Создание резервной копии текущей БД перед восстановлением
print_step "Создание резервной копии текущей БД перед восстановлением..."
SAFETY_BACKUP="$BACKUP_DIR/before_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
sudo -u postgres pg_dump $DB_NAME | gzip > $SAFETY_BACKUP
print_step "Страховочная копия создана: $SAFETY_BACKUP"

# Остановка приложения
print_step "Остановка приложения..."
systemctl stop shop-app

# Восстановление базы данных
print_step "Восстановление базы данных из: $BACKUP_FILE"

# Удаление и пересоздание базы данных
sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS ${DB_NAME}_temp;
CREATE DATABASE ${DB_NAME}_temp;
EOF

# Восстановление данных во временную БД
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | sudo -u postgres psql ${DB_NAME}_temp
else
    sudo -u postgres psql ${DB_NAME}_temp < $BACKUP_FILE
fi

# Переименование баз данных
sudo -u postgres psql <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS ${DB_NAME}_old;
ALTER DATABASE $DB_NAME RENAME TO ${DB_NAME}_old;
ALTER DATABASE ${DB_NAME}_temp RENAME TO $DB_NAME;
EOF

print_step "База данных восстановлена успешно!"

# Запуск приложения
print_step "Запуск приложения..."
systemctl start shop-app

sleep 3

# Проверка статуса
if systemctl is-active --quiet shop-app; then
    print_step "✅ Приложение успешно запущено!"
    
    # Удаление старой БД
    print_step "Удаление старой версии БД..."
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS ${DB_NAME}_old;"
    
    print_step "✅ Восстановление завершено успешно!"
else
    print_error "❌ Ошибка при запуске приложения!"
    print_error "Откатываем изменения..."
    
    # Откат изменений
    sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
ALTER DATABASE ${DB_NAME}_old RENAME TO $DB_NAME;
EOF
    
    systemctl start shop-app
    print_error "База данных возвращена к предыдущему состоянию"
    exit 1
fi

echo ""
print_step "Страховочная копия сохранена: $SAFETY_BACKUP"
print_step "Старую БД можно восстановить в течение следующих суток"
echo ""
