@echo off
chcp 65001 >nul
echo ========================================
echo   AI Customer Support Bot
echo ========================================
echo.

REM Переход в директорию ai_bot
cd /d "%~dp0"

REM Проверка наличия .env файла в корне проекта
if not exist ..\.env (
    echo [!] Файл .env не найден в корне проекта!
    echo.
    echo Создайте файл .env в корне проекта и добавьте:
    echo AI_BOT_TOKEN=ваш_токен_от_BotFather
    echo GEMINI_API_KEY=ваш_ключ_gemini
    echo DATABASE_URL=postgresql://user:password@localhost:5432/shop_db
    echo.
    pause
    exit /b 1
)

echo [1/1] Запуск AI бота...
echo.
echo ========================================
echo   Бот запускается...
echo ========================================
echo.

python ai_customer_bot.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   [!] Ошибка запуска бота. 
    echo   Попробуйте установить зависимости:
    echo   pip install google-generativeai pyTelegramBotAPI python-dotenv psycopg2-binary
    echo ========================================
    echo.
    pause
    exit /b 1
)
