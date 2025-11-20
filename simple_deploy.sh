#!/bin/bash

# Упрощенное развертывание на VPS одной командой
# Использование: curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/main/simple_deploy.sh | sudo bash

set -e

echo "=================================================="
echo "🚀 Установка Telegram Shop - Простой режим"
echo "=================================================="
echo ""

# Проверка root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Запустите с правами root: sudo bash simple_deploy.sh"
    exit 1
fi

# Спрашиваем источник кода
echo "📦 Откуда взять код?"
echo "1) GitHub репозиторий (рекомендуется)"
echo "2) Текущая директория"
echo ""
read -p "Выберите вариант [1]: " SOURCE_CHOICE
SOURCE_CHOICE=${SOURCE_CHOICE:-1}

GITHUB_REPO=""
if [ "$SOURCE_CHOICE" = "1" ]; then
    read -p "🔗 URL GitHub репозитория: " GITHUB_REPO
    if [ -z "$GITHUB_REPO" ]; then
        echo "❌ URL не может быть пустым"
        exit 1
    fi
fi

echo ""
echo "⚙️  Настройка приложения..."
echo ""

# Спрашиваем имя пользователя
read -p "👤 Имя пользователя для приложения [shopapp]: " APP_USER
APP_USER=${APP_USER:-shopapp}

# Спрашиваем пароль для БД
while true; do
    read -sp "🔐 Пароль для базы данных: " DB_PASSWORD
    echo ""
    if [ -z "$DB_PASSWORD" ]; then
        echo "❌ Пароль не может быть пустым"
        continue
    fi
    read -sp "🔐 Повторите пароль: " DB_PASSWORD_CONFIRM
    echo ""
    if [ "$DB_PASSWORD" = "$DB_PASSWORD_CONFIRM" ]; then
        break
    else
        echo "❌ Пароли не совпадают, попробуйте снова"
    fi
done

# Опционально: спрашиваем про домен
read -p "🌐 Ваш домен (оставьте пустым если нет): " DOMAIN

echo ""
echo "✅ Настройка завершена!"

# Автоматические параметры
DB_NAME="shop_db"
DB_USER="shop_user"
APP_PORT="5000"
APP_DIR="/home/$APP_USER/app"

echo "✅ Пользователь: $APP_USER"
echo "✅ База данных: $DB_NAME"
echo "✅ Порт: $APP_PORT"
echo ""

# Установка пакетов
echo "📦 Установка пакетов..."
export DEBIAN_FRONTEND=noninteractive
apt update -qq
apt install -y -qq python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl wget openssl > /dev/null 2>&1

# Node.js
if ! command -v node &> /dev/null; then
    echo "📦 Установка Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt install -y nodejs > /dev/null 2>&1
fi

# Создание пользователя
echo "👤 Создание пользователя..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$APP_USER"
fi
usermod -a -G www-data "$APP_USER"

# PostgreSQL
echo "🗄️  Настройка PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql > /dev/null 2>&1

sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME"
sudo -u postgres psql -c "SELECT 1 FROM pg_user WHERE usename = '$DB_USER'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER"

PG_VERSION=$(ls /etc/postgresql/ | head -n1)
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
if ! grep -q "host.*all.*all.*127.0.0.1/32.*md5" "$PG_HBA"; then
    echo "host    all             all             127.0.0.1/32            md5" >> "$PG_HBA"
    systemctl restart postgresql
fi

# Получение кода
if [ ! -z "$GITHUB_REPO" ]; then
    echo "📥 Загрузка из GitHub..."
    [ -d "$APP_DIR" ] && rm -rf "$APP_DIR"
    sudo -u "$APP_USER" git clone "$GITHUB_REPO" "$APP_DIR"
else
    echo "📁 Копирование файлов..."
    mkdir -p "$APP_DIR"
    cp -r ./* "$APP_DIR/" 2>/dev/null || true
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

cd "$APP_DIR"

# Установка зависимостей
echo "📦 Установка Python зависимостей..."
sudo -u "$APP_USER" python3 -m pip install --quiet --user -r requirements.txt

echo "📦 Установка Node.js зависимостей..."
sudo -u "$APP_USER" npm install --silent > /dev/null 2>&1

# Сборка фронтенда
echo "🔨 Сборка фронтенда..."
sudo -u "$APP_USER" npm run build

# Создание .env
echo "⚙️  Создание конфигурации..."
cat > "$APP_DIR/.env" <<EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
PORT=$APP_PORT
EOF
chown "$APP_USER:$APP_USER" "$APP_DIR/.env"

# Создание systemd сервиса
echo "🔧 Настройка systemd..."
cat > /etc/systemd/system/shop-app.service <<EOF
[Unit]
Description=Telegram Shop Application
After=network.target postgresql.service

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=/home/$APP_USER/.local/bin:/usr/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=/usr/bin/python3 -m gunicorn --bind 127.0.0.1:$APP_PORT --workers 2 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Настройка Nginx
echo "🌐 Настройка Nginx..."
if [ ! -z "$DOMAIN" ]; then
    SERVER_NAME="$DOMAIN"
else
    SERVER_NAME="_"
fi

cat > /etc/nginx/sites-available/shop-app <<EOF
server {
    listen 80;
    server_name $SERVER_NAME;
    
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/shop-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Запуск приложения
echo "🚀 Запуск приложения..."
systemctl daemon-reload
systemctl enable shop-app
systemctl restart shop-app

# Ожидание запуска
sleep 3

# Проверка статуса
if systemctl is-active --quiet shop-app; then
    echo ""
    echo "=================================================="
    echo "✅ УСТАНОВКА ЗАВЕРШЕНА!"
    echo "=================================================="
    echo ""
    if [ ! -z "$DOMAIN" ]; then
        echo "🌐 Ваш сайт: http://$DOMAIN"
    else
        IP=$(hostname -I | awk '{print $1}')
        echo "🌐 Ваш сайт: http://$IP"
    fi
    echo ""
    echo "📋 Полезные команды:"
    echo "  - Статус: systemctl status shop-app"
    echo "  - Логи: journalctl -u shop-app -f"
    echo "  - Перезапуск: systemctl restart shop-app"
    echo ""
    echo "🔐 Данные БД сохранены в: $APP_DIR/.env"
    echo ""
    
    if [ ! -z "$DOMAIN" ]; then
        echo "🔒 Для SSL сертификата выполните:"
        echo "   sudo apt install certbot python3-certbot-nginx -y"
        echo "   sudo certbot --nginx -d $DOMAIN"
    fi
else
    echo ""
    echo "❌ Ошибка запуска приложения"
    echo "Проверьте логи: journalctl -u shop-app -n 50"
    exit 1
fi
