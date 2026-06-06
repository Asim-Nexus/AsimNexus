@echo off
REM ASIMNEXUS Llama Server Startup Script
REM Starts llama-server.exe with Gemma 4 model

echo ========================================
echo ASIMNEXUS Llama Server Startup
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set ASIM_DIR=%SCRIPT_DIR%..

REM Configuration
set MODEL_PATH=%ASIM_DIR%\models\gemma-4-E4B-it-IQ4_XS.gguf
set LLAMA_SERVER=%ASIM_DIR%\llama.cpp\llama-server.exe
set HOST=127.0.0.1
set PORT=8080
set GPU_LAYERS=35
set CONTEXT_SIZE=2048
set THREADS=4

echo Model Path: %MODEL_PATH%
echo Llama Server: %LLAMA_SERVER%
echo Host: %HOST%:%PORT%
echo GPU Layers: %GPU_LAYERS%
echo Context Size: %CONTEXT_SIZE%
echo Threads: %THREADS%
echo.

REM Check if model exists
if not exist "%MODEL_PATH%" (
    echo ERROR: Model file not found: %MODEL_PATH%
    echo Please download the Gemma 4 model first.
    pause
    exit /b 1
)

REM Check if llama-server.exe exists
if not exist "%LLAMA_SERVER%" (
    echo ERROR: llama-server.exe not found: %LLAMA_SERVER%
    echo Please ensure llama.cpp is properly installed.
    pause
    exit /b 1
)

echo Starting llama-server.exe...
echo.

REM Start llama-server.exe
"%LLAMA_SERVER%" ^
    -m "%MODEL_PATH%" ^
    --host %HOST% ^
    --port %PORT% ^
    --gpu-layers %GPU_LAYERS% ^
    -c %CONTEXT_SIZE% ^
    -t %THREADS% ^
    --log-format text

pause
