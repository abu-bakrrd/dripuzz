@echo off
chcp 65001 >nul
echo ================================================
echo 🚀 Сборка Telegram бота в EXE файл
echo ================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8 или новее
    echo Скачать: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python найден
echo.

REM Установка PyInstaller и зависимостей
echo 📦 Установка зависимостей...
python -m pip install --upgrade pip --quiet
python -m pip install pyinstaller --quiet
python -m pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ❌ Ошибка установки зависимостей
    pause
    exit /b 1
)

echo ✅ Зависимости установлены
echo.

REM Сборка exe файла
echo 🔨 Сборка exe файла...
echo Это может занять несколько минут...
echo.

pyinstaller bot.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ❌ Ошибка сборки
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ Сборка завершена успешно!
echo ================================================
echo.
echo 📂 Файл находится в папке: dist\
echo 📄 Имя файла: TelegramShopBot.exe
echo.
echo 📋 Перед запуском:
echo    1. Скопируйте файл .env в папку dist\
echo    2. Скопируйте файл settingsbot.json в папку dist\
echo    3. Запустите TelegramShopBot.exe
echo.
echo ================================================
pause
