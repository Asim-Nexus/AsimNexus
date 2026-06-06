
@echo off
echo 🚀 ASIMNEXUS Universal Installer - Windows
echo ========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Installing Python...
    start /wait https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    echo ✅ Python installed successfully
)

REM Create virtual environment
echo 📁 Creating virtual environment...
python -m venv asimnexus_env
call asimnexus_env\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Initialize ASIMNEXUS
echo 🧠 Initializing ASIMNEXUS...
python main.py --init

REM Start services
echo 🚀 Starting ASIMNEXUS services...
python start_asimnexus_complete.py

echo ✅ ASIMNEXUS installation complete!
echo 🌐 Access at: http://localhost:8080
echo 🔍 Dashboard at: http://localhost:8080/frontend/dashboard.html
pause
