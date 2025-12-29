@echo off
title MiniTasker Shop Bot
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo ========================================
echo  Запуск Telegram Магазин Бота
echo ========================================
echo.

REM Переход в корень проекта
cd /d "%~dp0.."

REM Проверка наличия .env файла
if not exist .env (
    echo [!] Файл .env не найден!
    echo.
    echo Создайте файл .env с необходимыми переменными окружения.
    echo.
    pause
    exit /b 1
)

echo Запуск telegram_bot/telegrambot.py...
python telegram_bot/telegrambot.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo  [!] Бот остановился с ошибкой
    echo ========================================
    echo.
    pause
)
