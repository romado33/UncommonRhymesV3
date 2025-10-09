@echo off
REM ============================================================================
REM RhymeRarity - Quick Start Script
REM ============================================================================

echo.
echo ============================================================================
echo STARTING RHYMERARITY
echo ============================================================================
echo.

REM Create logs directory if it doesn't exist
if not exist "logs\" mkdir logs

REM Start the app
echo Starting Gradio server...
echo.
echo Once started, open your browser to:
echo   http://127.0.0.1:7860
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================================
echo.

python app.py

echo.
echo ============================================================================
echo Server stopped.
echo ============================================================================
echo.
pause
