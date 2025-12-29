@echo off
title MiniTasker AI Bot
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo ========================================
echo   AI Customer Support Bot
echo ========================================
echo.

REM Переход в корень проекта
cd /d "%~dp0.."

REM Проверка наличия .env файла
if not exist .env (
    echo [!] Файл .env не найден!
    echo.
    echo Создайте файл .env и добавьте:
    echo AI_BOT_TOKEN=ваш_токен_от_BotFather
    echo GEMINI_API_KEY=ваш_ключ_gemini
    echo DATABASE_URL=postgresql://user:password@localhost:5432/shop_db
    echo.
    pause
    exit /b 1
)

echo [1/2] Проверка зависимостей...
pip show google-generativeai >nul 2>&1
if errorlevel 1 (
    echo.
    echo [!] Библиотека google-generativeai не установлена!
    echo.
    echo Установить сейчас? (Y/N)
    set /p install_deps=
    if /i "%install_deps%"=="Y" (
        echo.
        echo Установка зависимостей...
        pip install google-generativeai pyTelegramBotAPI python-dotenv psycopg2-binary
        echo.
    ) else (
        echo.
        echo Установите зависимости вручную:
        echo pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo [2/2] Запуск AI бота...
echo.
echo ========================================
echo   Бот запускается...
echo ========================================
echo.

python ai_bot/ai_customer_bot.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   [!] Ошибка запуска бота
    echo ========================================
    echo.
    pause
    exit /b 1
)
