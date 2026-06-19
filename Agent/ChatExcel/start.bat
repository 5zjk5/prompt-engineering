@echo off
echo ========================================
echo   Chat Excel - Starting...
echo ========================================

echo.
echo [1/2] Starting backend (port 7396)...
cd /d "%~dp0backend"
start "Chat Excel Backend" cmd /k ""C:\Users\13479\AppData\Local\Programs\Python\Python314\python.exe" main.py & pause"

echo [2/2] Starting frontend (port 3030)...
cd /d "%~dp0frontend"
start "Chat Excel Frontend" cmd /c "npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:7396
echo   Frontend: http://localhost:3030
echo   API Docs: http://localhost:7396/docs
echo ========================================
echo.
start http://localhost:3030
