@echo off
REM ============================================================================
REM RhymeRarity - Windows Installation Script
REM ============================================================================

echo.
echo ============================================================================
echo RHYMERARITY - AUTOMATED SETUP
echo ============================================================================
echo.

REM Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python found!
echo.

REM Install dependencies
echo [2/4] Installing dependencies...
echo Installing: gradio requests wordfreq cmudict
pip install gradio requests wordfreq cmudict
if errorlevel 1 (
    echo [WARNING] Installation had errors, trying with --user flag...
    pip install --user gradio requests wordfreq cmudict
)
echo [OK] Dependencies installed!
echo.

REM Verify module structure
echo [3/4] Verifying module structure...
if not exist "rhyme_core\" (
    echo [ERROR] rhyme_core folder not found!
    echo Please make sure you extracted all files correctly.
    pause
    exit /b 1
)
if not exist "rhyme_core\engine.py" (
    echo [ERROR] engine.py not found in rhyme_core!
    pause
    exit /b 1
)
if not exist "rhyme.db" (
    echo [ERROR] rhyme.db not found!
    echo Run: python build_rhyme_database.py
    pause
    exit /b 1
)
echo [OK] All files present!
echo.

REM Test imports
echo [4/4] Testing imports...
python -c "from rhyme_core.engine import search_rhymes; print('[OK] Imports working!')"
if errorlevel 1 (
    echo [ERROR] Import test failed!
    pause
    exit /b 1
)
echo.

echo ============================================================================
echo INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo To start the app:
echo   python app.py
echo.
echo Then open your browser to:
echo   http://127.0.0.1:7860
echo.
echo ============================================================================
echo.
pause
