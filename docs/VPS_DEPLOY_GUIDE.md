# 🚀 Инструкция по развертыванию на VPS Ubuntu 22.04

> [!IMPORTANT] > **Мастер-установка (РЕКОМЕНДУЕТСЯ)** 🔥
> Если вы хотите установить всё (сайт + все боты + SSL) одной командой, используйте:
>
> ```bash
> sudo ./scripts/master_deploy.sh
> ```
>
> Подробнее: [БЫСТРАЯ_УСТАНОВКА.md](file:///c%3A/MiniTaskerBot3/docs/%D0%91%D0%AB%D0%A1%D0%A2%D0%A0%D0%90%D0%AF_%D0%A3%D0%A1%D0%A2%D0%90%D0%9D%D0%9E%D0%92%D0%9A%D0%90.md)

## Информация о VPS

- **IP**: YOUR_VPS_IP
- **ОС**: Ubuntu 22.04
- **База данных**: PostgreSQL (локально на VPS)

---

## 📋 Шаг 1: Подключение к VPS и начальная настройка

```bash
# Подключитесь к VPS по SSH
ssh root@YOUR_VPS_IP

# Обновите систему
apt update && apt upgrade -y

# Установите необходимые пакеты
apt install -y python3 python3-pip python3-venv nodejs npm postgresql postgresql-contrib nginx git curl
```

---

## 🗄️ Шаг 2: Настройка PostgreSQL

```bash
# Переключитесь на пользователя postgres
sudo -u postgres psql

# В psql выполните:
CREATE DATABASE shop_db;
CREATE USER shop_user WITH PASSWORD 'ваш_надежный_пароль';
GRANT ALL PRIVILEGES ON DATABASE shop_db TO shop_user;
\q

# Разрешите локальные подключения
# Отредактируйте pg_hba.conf
nano /etc/postgresql/14/main/pg_hba.conf

# Добавьте или измените строку для локального подключения:
# local   all             all                                     md5
# host    all             all             127.0.0.1/32            md5

# Перезапустите PostgreSQL
systemctl restart postgresql
```

---

## 📁 Шаг 3: Подготовка приложения

```bash
# Создайте пользователя для приложения (опционально, но рекомендуется)
adduser --disabled-password --gecos "" shopapp
usermod -aG sudo shopapp

# Переключитесь на нового пользователя
su - shopapp

# Создайте директорию для приложения
mkdir -p /home/shopapp/app
cd /home/shopapp/app

# Загрузите код приложения (один из вариантов):
# Вариант 1: Клонирование из git (если у вас есть репозиторий)
# git clone https://github.com/your-repo/shop.git .

# Вариант 2: Загрузка через SCP с вашего локального компьютера
# На вашем локальном компьютере выполните:
# scp -r /путь/к/проекту/* shopapp@YOUR_VPS_IP:/home/shopapp/app/

# Вариант 3: Загрузка из Replit
# Можно использовать git или архив
```

---

## 🔧 Шаг 4: Настройка переменных окружения

```bash
# Создайте файл .env в директории приложения
nano /home/shopapp/app/.env

# Добавьте следующие переменные:
DATABASE_URL=postgresql://shop_user:ваш_надежный_пароль@localhost:5432/shop_db
PORT=5000
FLASK_ENV=production
```

---

## 📦 Шаг 5: Установка зависимостей и сборка

```bash
cd /home/shopapp/app

# Установите Node.js зависимости
npm install

# Соберите фронтенд
npm run build

# Создайте виртуальное окружение Python
python3 -m venv venv
source venv/bin/activate

# Установите Python зависимости
pip install -r requirements.txt

# Инициализируйте базу данных (таблицы создадутся автоматически при первом запуске)
# Но можно запустить вручную:
python3 app.py &
sleep 5
pkill -f app.py

# Загрузите тестовые данные (опционально)
python3 seed_db.py
```

---

## 🔄 Шаг 6: Настройка systemd сервиса

```bash
# Вернитесь к root или используйте sudo
exit  # если вы были под пользователем shopapp

# Создайте systemd unit file для Flask приложения
sudo nano /etc/systemd/system/shop-app.service
```

Содержимое файла:

```ini
[Unit]
Description=Telegram Shop Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=shopapp
WorkingDirectory=/home/shopapp/app
Environment="PATH=/home/shopapp/app/venv/bin"
EnvironmentFile=/home/shopapp/app/.env
ExecStart=/home/shopapp/app/venv/bin/gunicorn app:app --bind 127.0.0.1:5000 --workers 4 --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Перезагрузите systemd и запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable shop-app
sudo systemctl start shop-app

# Проверьте статус
sudo systemctl status shop-app
```

---

## 🌐 Шаг 7: Настройка Nginx

```bash
# Создайте конфигурацию Nginx
sudo nano /etc/nginx/sites-available/shop
```

Содержимое файла:

```nginx
server {
    listen 80;
    server_name YOUR_VPS_IP;

    # Максимальный размер загружаемых файлов
    client_max_body_size 20M;

    # Логи
    access_log /var/log/nginx/shop_access.log;
    error_log /var/log/nginx/shop_error.log;

    # Статические файлы
    location /assets {
        alias /home/shopapp/app/dist/public/assets;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /config {
        alias /home/shopapp/app/config;
        expires 1h;
        add_header Cache-Control "public";
    }

    # Проксирование запросов к Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Увеличиваем таймауты для длительных запросов
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

```bash
# Активируйте конфигурацию
sudo ln -s /etc/nginx/sites-available/shop /etc/nginx/sites-enabled/

# Удалите дефолтную конфигурацию (опционально)
sudo rm /etc/nginx/sites-enabled/default

# Проверьте конфигурацию Nginx
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

---

## 🔐 Шаг 8: Настройка SSL (опционально, но рекомендуется)

Если у вас есть доменное имя, вы можете настроить SSL с помощью Let's Encrypt:

```bash
# Установите Certbot
sudo apt install -y certbot python3-certbot-nginx

# Получите SSL сертификат (замените yourdomain.com на ваш домен)
sudo certbot --nginx -d yourdomain.com

# Certbot автоматически обновит конфигурацию Nginx
# Для автоматического обновления сертификатов добавьте cron job:
sudo certbot renew --dry-run
```

---

## 🤖 Шаг 9: Настройка Telegram Bot (опционально)

Если вам нужен Telegram бот:

```bash
# Создайте systemd сервис для бота
sudo nano /etc/systemd/system/shop-bot.service
```

Содержимое файла:

```ini
[Unit]
Description=Telegram Shop Bot
After=network.target

[Service]
Type=simple
User=shopapp
WorkingDirectory=/home/shopapp/app
Environment="PATH=/home/shopapp/app/venv/bin"
EnvironmentFile=/home/shopapp/app/.env
ExecStart=/home/shopapp/app/venv/bin/python3 telegrambot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Не забудьте добавить BOT_TOKEN в .env файл!
# Затем запустите бот:
sudo systemctl daemon-reload
sudo systemctl enable shop-bot
sudo systemctl start shop-bot
sudo systemctl status shop-bot
```

---

## 🛡️ Шаг 10: Настройка Firewall

```bash
# Установите UFW (если еще не установлен)
sudo apt install -y ufw

# Разрешите SSH, HTTP и HTTPS
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Включите firewall
sudo ufw enable

# Проверьте статус
sudo ufw status
```

---

## ✅ Проверка работы

```bash
# Проверьте статус всех сервисов
sudo systemctl status shop-app
sudo systemctl status nginx
sudo systemctl status postgresql

# Проверьте логи
sudo journalctl -u shop-app -f
sudo tail -f /var/log/nginx/shop_error.log

# Откройте в браузере:
# http://YOUR_VPS_IP
```

---

## 🔧 Полезные команды для управления

```bash
# Перезапуск приложения
sudo systemctl restart shop-app

# Просмотр логов приложения
sudo journalctl -u shop-app -f

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/shop_access.log
sudo tail -f /var/log/nginx/shop_error.log

# Обновление кода приложения
cd /home/shopapp/app
git pull  # если используете git
npm install
npm run build
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart shop-app

# Резервное копирование базы данных
sudo -u postgres pg_dump shop_db > backup_$(date +%Y%m%d).sql

# Восстановление базы данных
sudo -u postgres psql shop_db < backup_20241107.sql
```

---

## 🐛 Устранение проблем

### Приложение не запускается

```bash
# Проверьте логи
sudo journalctl -u shop-app -n 100

# Проверьте права доступа
ls -la /home/shopapp/app

# Проверьте подключение к БД
psql -U shop_user -d shop_db -h localhost
```

### Nginx показывает 502 Bad Gateway

```bash
# Проверьте, запущен ли Flask
sudo systemctl status shop-app

# Проверьте, слушает ли приложение на порту 5000
sudo netstat -tulpn | grep 5000

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/shop_error.log
```

### База данных не подключается

```bash
# Проверьте, запущен ли PostgreSQL
sudo systemctl status postgresql

# Проверьте настройки подключения в .env
cat /home/shopapp/app/.env

# Проверьте pg_hba.conf
sudo cat /etc/postgresql/14/main/pg_hba.conf
```

---

## 📊 Мониторинг

Для мониторинга производительности можно установить:

```bash
# htop для мониторинга системы
sudo apt install -y htop

# Запустите htop
htop
```

---

## 🎉 Готово!

Ваше приложение теперь развернуто на VPS и доступно по адресу:

- **HTTP**: http://YOUR_VPS_IP
- **HTTPS** (если настроили SSL): https://yourdomain.com

Все данные и база данных находятся локально на вашем VPS.
