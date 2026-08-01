@echo off
title ANPR System Startup
color 0A
echo.
echo ========================================
echo    🚀 ANPR System Complete Startup
echo ========================================
echo.

cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    echo 🔌 Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo 📦 Installing/Updating dependencies...
python -m pip install -r requirements.txt --quiet --upgrade

echo.
echo 🔗 Starting MongoDB Atlas Service...
start "Atlas Service" cmd /k "if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) & python -u backend/services/atlas_service.py"

echo ⏳ Waiting for Atlas service to initialize...
ping 127.0.0.1 -n 6 >nul

echo.
echo 🎯 Starting ANPR Web Application...
echo 📋 System will be available at: http://127.0.0.1:5000
echo 📊 Performance metrics: http://127.0.0.1:5000/api/performance
echo 🔗 Atlas status: http://127.0.0.1:5000/api/atlas/status
echo.
echo ✅ System starting... Please wait for "Running on http://127.0.0.1:5000"
echo.

python -u backend/api/web_app.py

pause
