# Информационный Telegram Бот

Простой Telegram бот для ответов на команды.

## Команды

- `/start` - Приветствие и список команд
- `/about` - О компании/магазине
- `/help` - Справка по командам
- `/support` - Поддержка
- `/contact` - Контактная информация

## Настройка

1. Создайте бота через @BotFather и получите токен
2. Отредактируйте файл `.env`:
   ```
   INFO_BOT_TOKEN=ваш_токен_от_BotFather
   ```
3. Отредактируйте тексты ответов в `main.py`

## Запуск локально

```bash
# Установка зависимостей
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Запуск
python main.py
```

## Запуск на VPS

Бот автоматически устанавливается через `deploy_vps.sh` если выбрана опция установки.

### Управление сервисом

```bash
# Статус
systemctl status info-bot

# Логи
journalctl -u info-bot -f

# Перезапуск
systemctl restart info-bot

# Остановка
systemctl stop info-bot
```

## Редактирование текстов

Все тексты ответов находятся в `main.py` в функциях:
- `start_command()` - текст приветствия
- `about_command()` - информация о компании
- `help_command()` - справка
- `support_command()` - поддержка
- `contact_command()` - контакты

После изменения текстов перезапустите бота:
```bash
systemctl restart info-bot
```
