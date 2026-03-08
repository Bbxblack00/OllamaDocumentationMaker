@echo off
:: setup.bat — Bootstrap ai-doc-gen on Windows
setlocal EnableDelayedExpansion

set VENV_DIR=.venv

echo.
echo ╔══════════════════════════════════════╗
echo ║   🔧  ai-doc-gen Setup (Windows)    ║
echo ╚══════════════════════════════════════╝
echo.

:: 1. Create venv
if not exist "%VENV_DIR%\" (
    echo [STEP] Creating virtual environment...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Is Python installed and in PATH?
        exit /b 1
    )
    echo [OK] venv created at .\%VENV_DIR%
) else (
    echo [OK] venv already exists -- skipping
)

:: 2. Activate & install
echo [STEP] Installing dependencies...
call %VENV_DIR%\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo [OK] Dependencies installed

echo.
echo ╔══════════════════════════════════════╗
echo ║       ✅  Setup complete!            ║
echo ╚══════════════════════════════════════╝
echo.
echo   Activate venv :  .venv\Scripts\activate
echo   Run           :  python main.py C:\path\to\project
echo   Options       :  python main.py --help
echo.

endlocal
