# Инструкция по деплою на Render

## Проблема
Flask приложение запускается, но возвращает 404 на главной странице, потому что фронтенд не собран.

## Решение

### 1. Настройте Build Command в Render:
```bash
./build.sh
```

### 2. Настройте Start Command:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 4 --timeout 120
```

### 3. Переменные окружения:
Убедитесь, что установлены:
- `DATABASE_URL` - URL подключения к PostgreSQL

### 4. Файлы проекта:
- ✅ `requirements.txt` - Python зависимости
- ✅ `build.sh` - скрипт для сборки фронтенда
- ✅ `app.py` - Flask приложение
- ✅ `package.json` - Node.js зависимости

## Как это работает:

1. **Build phase**: 
   - Render запускает `./build.sh`
   - Устанавливаются Node.js зависимости
   - Собирается фронтенд в `dist/public/`
   - Устанавливаются Python зависимости из `requirements.txt`

2. **Start phase**:
   - Запускается gunicorn с Flask приложением
   - Flask обслуживает статические файлы из `dist/public/`
   - API endpoints доступны по `/api/*`

## Проверка:
После деплоя:
- Главная страница (/) должна показывать React приложение
- API endpoints (/api/*) должны работать
