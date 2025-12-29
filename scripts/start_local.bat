@echo off
echo ========================================
echo   MiniTaskerBot3 - Локальный запуск
echo ========================================
echo.

echo [1/2] Запуск Flask сервера...
start "Flask Server" cmd /k "cd /d %~dp0.. && python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Запуск Vite dev сервера...
start "Vite Dev Server" cmd /k "cd /d %~dp0.. && npm run dev"

echo.
echo ========================================
echo   ✅ Проект запущен!
echo ========================================
echo.
echo 🌐 Откройте в браузере:
echo    http://localhost:5173
echo.
echo 📊 API доступен на:
echo    http://localhost:5000
echo.
echo 👨‍💼 Админ-панель:
echo    http://localhost:5173/admin
echo.
echo ========================================
echo.
echo Для остановки закройте оба окна сервера
echo.
pause
