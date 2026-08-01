@echo off
echo 🚀 Starting MongoDB Atlas Service for ANPR System...
echo.

cd /d "%~dp0"

if exist .venv\Scripts\activate.bat (
    echo 🔌 Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo 📋 Activating Python environment...
call python -m pip install schedule pymongo certifi --quiet

echo 🔗 Starting Atlas Service...
python backend/services/atlas_service.py

pause
