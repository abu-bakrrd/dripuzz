#!/bin/bash

# Скрипт автоматического развертывания Telegram Shop + AI Bot на VPS
# Использование: ./deploy_vps.sh

set -e

# ==========================================
# 1. ПОДТВЕРЖДЕНИЕ УСТАНОВКИ
# ==========================================
echo "=================================================="
echo "🚀 Начало установки MiniTaskerBot3 на VPS"
echo "=================================================="
echo ""
echo "Этот скрипт установит:"
echo "  1. Python, PostgreSQL, Nginx, Node.js"
echo "  2. Flask Web App (Интернет-магазин)"
echo "  3. Telegram Shop Bot (Основной бот магазина)"
echo "  4. AI Bot 'Mona' (Поддержка клиентов)"
echo "  5. Настроит базы данных и systemd сервисы"
echo ""
read -p "❓ Вы хотите продолжить установку? (y/n): " CONFIRM_INSTALL
if [[ "$CONFIRM_INSTALL" != "y" && "$CONFIRM_INSTALL" != "Y" ]]; then
    echo "❌ Установка отменена пользователем."
    exit 0
fi

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка, что скрипт запущен с правами root
if [ "$EUID" -ne 0 ]; then 
    print_error "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Запрос параметров
echo ""
echo "🔗 НАСТРОЙКА ИСТОЧНИКА КОДА"
echo ""
read -p "Введите URL вашего GitHub репозитория (или оставьте пустым для локальных файлов): " GITHUB_REPO
echo ""

if [ ! -z "$GITHUB_REPO" ]; then
    read -p "Введите ветку для клонирования [main]: " GIT_BRANCH
    GIT_BRANCH=${GIT_BRANCH:-main}
    echo ""
    print_step "Будет использован репозиторий: $GITHUB_REPO (ветка: $GIT_BRANCH)"
else
    print_step "Будут использованы локальные файлы"
fi

echo ""
echo "⚙️ НАСТРОЙКА ПРИЛОЖЕНИЯ"
echo ""

read -p "Введите имя пользователя для приложения [shopapp]: " APP_USER
APP_USER=${APP_USER:-shopapp}
# Валидация имени пользователя
if [[ ! "$APP_USER" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    print_error "Некорректное имя пользователя. Используется значение по умолчанию: shopapp"
    APP_USER="shopapp"
fi

read -p "Введите имя базы данных [shop_db]: " DB_NAME
DB_NAME=${DB_NAME:-shop_db}

read -p "Введите имя пользователя БД [shop_user]: " DB_USER
DB_USER=${DB_USER:-shop_user}

read -sp "Введите пароль для БД: " DB_PASSWORD
echo
# Проверка пароля
if [ -z "$DB_PASSWORD" ]; then
    print_error "Пароль не может быть пустым!"
    read -sp "Введите пароль для БД ещё раз: " DB_PASSWORD
    echo
fi

read -p "Введите порт для приложения [5000]: " APP_PORT
APP_PORT=${APP_PORT:-5000}

echo ""
echo "🤖 НАСТРОЙКА AI БОТА (MONA)"
echo ""
read -p "Введите Telegram TOKEN для Основного Shop Бота: " TELEGRAM_BOT_TOKEN
read -p "Введите Telegram TOKEN для AI Бота (Mona): " AI_BOT_TOKEN
read -p "Введите GROQ API KEY (для Llama): " GROQ_API_KEY
read -p "Введите GEMINI API KEY (резерв/опция): " GEMINI_API_KEY
echo ""

print_step "Настройки сохранены"

# Установка пакетов
print_step "Обновление системы и установка пакетов..."
apt update && apt upgrade -y

print_step "Установка необходимых пакетов..."
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl

# Node.js
if ! command -v node &> /dev/null; then
    print_step "Установка Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
else
    print_step "Node.js уже установлен: $(node --version)"
fi

# Создание пользователя приложения
print_step "Создание пользователя приложения: $APP_USER"
if id "$APP_USER" &>/dev/null; then
    print_warning "Пользователь $APP_USER уже существует"
else
    adduser --disabled-password --gecos "" --quiet $APP_USER 2>/dev/null || \
    useradd -m -s /bin/bash $APP_USER
    if id "$APP_USER" &>/dev/null; then
        print_step "Пользователь $APP_USER создан"
    else
        print_error "Не удалось создать пользователя $APP_USER"
        exit 1
    fi
fi

# Добавление пользователя в группу www-data
usermod -a -G www-data $APP_USER
print_step "Пользователь $APP_USER добавлен в группу www-data"

# Настройка PostgreSQL
print_step "Настройка PostgreSQL..."
sudo -u postgres psql <<EOF
-- Создание базы данных и пользователя
SELECT 'CREATE DATABASE $DB_NAME' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
DO
\$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;
EOF

print_step "PostgreSQL настроен"

# Настройка pg_hba.conf для локальных подключений
PG_VERSION=$(ls /etc/postgresql/)
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

if ! grep -q "host.*all.*all.*127.0.0.1/32.*md5" "$PG_HBA"; then
    print_step "Настройка pg_hba.conf..."
    echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
    systemctl restart postgresql
fi

# Создание директории приложения и получение кода
APP_DIR="/home/$APP_USER/app"

if [ ! -z "$GITHUB_REPO" ]; then
    print_step "Клонирование репозитория из GitHub: $GITHUB_REPO"
    if [ -d "$APP_DIR" ]; then
        print_warning "Директория $APP_DIR уже существует, удаляем..."
        rm -rf $APP_DIR
    fi
    sudo -u $APP_USER git clone -b $GIT_BRANCH $GITHUB_REPO $APP_DIR
    if [ $? -ne 0 ]; then
        print_error "Ошибка клонирования репозитория"
        exit 1
    fi
    print_step "Репозиторий успешно клонирован"
else
    print_step "Создание директории приложения: $APP_DIR"
    mkdir -p $APP_DIR
    print_step "Копирование файлов приложения..."
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    # Копируем всё из родительской папки (предполагаем, что скрипт в /scripts)
    cp -r $SCRIPT_DIR/../* $APP_DIR/ 2>/dev/null || true
    chown -R $APP_USER:$APP_USER $APP_DIR
    print_step "Локальные файлы скопированы"
fi

# Создание .env файла
print_step "Создание файла .env..."
SESSION_SECRET=$(openssl rand -hex 32)
cat > $APP_DIR/.env <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
PORT=$APP_PORT
FLASK_ENV=production
SESSION_SECRET=$SESSION_SECRET

# Bot Configurations
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
AI_BOT_TOKEN=$AI_BOT_TOKEN
GROQ_API_KEY=$GROQ_API_KEY
GEMINI_API_KEY=$GEMINI_API_KEY
EOF

chown $APP_USER:$APP_USER $APP_DIR/.env
chmod 600 $APP_DIR/.env

print_step "Файл .env создан"

# Установка зависимостей
print_step "Установка зависимостей..."
cd $APP_DIR

# Frontend
sudo -u $APP_USER bash <<EOF
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd $APP_DIR
if [ -f "package.json" ]; then
    npm install
    npm run build
fi
EOF

# Backend (Python)
sudo -u $APP_USER bash <<EOF
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF

# Инициализация таблиц
print_step "Инициализация таблиц базы данных..."
sudo -u $APP_USER bash <<EOF
cd $APP_DIR
source venv/bin/activate
python3 scripts/init_tables.py
EOF

# Настройка прав для Nginx
chmod 755 /home/$APP_USER
chmod 755 $APP_DIR
if [ -d "$APP_DIR/dist" ]; then
    chown -R $APP_USER:www-data $APP_DIR/dist
    chmod -R 755 $APP_DIR/dist
fi

# ==========================================
# СОЗДАНИЕ СЕРВИСОВ (SYSTEMD)
# ==========================================

print_step "Создание сервиса Flask (Магазин)..."
cat > /etc/systemd/system/shop-app.service <<EOF
[Unit]
Description=Telegram Shop Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn app:app --bind 127.0.0.1:$APP_PORT --workers 4 --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_step "Создание сервиса Shop Bot (telegram-bot)..."
cat > /etc/systemd/system/telegram-bot.service <<EOF
[Unit]
Description=Telegram Shop Bot
After=network.target postgresql.service shop-app.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/python3 telegram_bot/telegrambot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Запуск сервисов
print_step "Запуск сервисов..."
systemctl daemon-reload

systemctl enable shop-app
systemctl enable ai-bot
systemctl enable telegram-bot

systemctl restart shop-app
systemctl restart ai-bot
systemctl restart telegram-bot

# Проверка статуса
sleep 3
if systemctl is-active --quiet shop-app; then
    print_step "✅ Магазин (Flask) запущен!"
else
    print_error "❌ Ошибка запуска Магазина! Проверьте логи: journalctl -u shop-app"
fi

if systemctl is-active --quiet ai-bot; then
    print_step "✅ AI Бот (Mona) запущен!"
else
    print_error "❌ Ошибка запуска AI Бота! Проверьте логи: journalctl -u ai-bot"
fi

if systemctl is-active --quiet telegram-bot; then
    print_step "✅ Основной Shop Бот запущен!"
else
    print_error "❌ Ошибка запуска Shop Бота! Проверьте логи: journalctl -u telegram-bot"
fi

# Настройка Nginx
print_step "Настройка Nginx..."
cat > /etc/nginx/sites-available/shop <<EOF
server {
    listen 80;
    server_name _;
    client_max_body_size 20M;

    access_log /var/log/nginx/shop_access.log;
    error_log /var/log/nginx/shop_error.log;

    location /assets {
        alias $APP_DIR/dist/public/assets;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /config {
        alias $APP_DIR/config;
        expires 1h;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

if nginx -t; then
    systemctl restart nginx
    print_step "Nginx конфигурация успешно обновлена"
else
    print_error "Ошибка конфига Nginx"
fi

echo ""
echo "=================================================="
echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
echo "=================================================="
echo "1. Сайт и Магазин: http://$(hostname -I | awk '{print $1}')"
echo "2. AI Бот: Запущен в Telegram"
echo ""
echo "📜 ЛОГИ:"
echo "   - Магазин: sudo journalctl -u shop-app -f"
echo "   - AI Бот:  sudo journalctl -u ai-bot -f"
echo "   - Shop Бот: sudo journalctl -u telegram-bot -f"
echo ""
