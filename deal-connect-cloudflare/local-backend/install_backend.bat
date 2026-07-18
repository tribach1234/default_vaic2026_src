@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Khong tim thay Python Launcher ^(py.exe^).
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Tao virtual environment...
    py -m venv .venv
    if errorlevel 1 goto :error
)

call ".venv\Scripts\activate.bat"
python --version
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error

pip install -r requirements.txt
if errorlevel 1 goto :error

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo [IMPORTANT] Da tao file .env. Hay mo file nay va dien API key/origin truoc khi chay.
)

echo.
echo Cai dat hoan tat.
pause
exit /b 0

:error
echo.
echo Cai dat that bai. Xem loi o phia tren.
pause
exit /b 1
