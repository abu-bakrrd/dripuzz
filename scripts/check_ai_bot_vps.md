# 🔍 Проверка AI Бота (Mona) на VPS

## Быстрая проверка

```bash
# Запустите скрипт проверки
sudo bash scripts/check_ai_bot_vps.sh
```

## Ручная проверка

### 1. Проверка статуса сервиса

```bash
sudo systemctl status ai-bot
```

Должно показать:
```
● ai-bot.service - AI Customer Support Bot
   Loaded: loaded (/etc/systemd/system/ai-bot.service; enabled)
   Active: active (running) since ...
```

### 2. Просмотр логов в реальном времени

```bash
sudo journalctl -u ai-bot -f
```

### 3. Последние логи (50 строк)

```bash
sudo journalctl -u ai-bot -n 50
```

### 4. Логи за последний час

```bash
sudo journalctl -u ai-bot --since "1 hour ago"
```

### 5. Поиск ошибок

```bash
sudo journalctl -u ai-bot | grep -i error
```

### 6. Проверка конфигурации

```bash
# Проверка .env файла
cd /home/shopapp/app
cat .env | grep -E "AI_BOT_TOKEN|GROQ_API_KEY"
```

## Управление ботом

### Перезапуск

```bash
sudo systemctl restart ai-bot
```

### Остановка

```bash
sudo systemctl stop ai-bot
```

### Запуск

```bash
sudo systemctl start ai-bot
```

### Проверка после перезапуска

```bash
sleep 3
sudo systemctl status ai-bot
```

## Типичные проблемы

### Бот не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u ai-bot -n 50
   ```

2. Проверьте переменные окружения:
   ```bash
   cd /home/shopapp/app
   cat .env | grep GROQ_API_KEY
   ```

3. Проверьте зависимости:
   ```bash
   cd /home/shopapp/app
   source venv/bin/activate
   pip list | grep groq
   ```

### Бот падает с ошибками

1. Посмотрите полные логи:
   ```bash
   sudo journalctl -u ai-bot --since "10 minutes ago" | tail -100
   ```

2. Проверьте подключение к БД:
   ```bash
   cd /home/shopapp/app
   source venv/bin/activate
   python3 -c "from ai_bot.ai_db_helper import get_all_products_info; print(len(get_all_products_info()))"
   ```

## Полезные команды

```bash
# Все логи за сегодня
sudo journalctl -u ai-bot --since today

# Логи с определенного времени
sudo journalctl -u ai-bot --since "2024-01-15 10:00:00"

# Экспорт логов в файл
sudo journalctl -u ai-bot --since "1 hour ago" > bot_logs.txt

# Мониторинг в реальном времени с фильтром
sudo journalctl -u ai-bot -f | grep -E "ERROR|WARNING|✅|❌"
```

