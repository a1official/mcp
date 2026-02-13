@echo off
echo Installing Python MCP Server Dependencies...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Install dependencies
echo Installing FastMCP and dependencies...
pip install fastmcp httpx

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run the application with:
echo   npm run dev
echo.
pause
