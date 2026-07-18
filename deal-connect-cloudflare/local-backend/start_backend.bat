@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Chua cai dependencies. Hay chay install_backend.bat truoc.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [ERROR] Chua co file .env. Hay copy .env.example thanh .env va cau hinh.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python server.py
pause
