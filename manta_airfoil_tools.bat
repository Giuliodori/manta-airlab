@echo off
cd /d "%~dp0"

title Manta AirLab

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw manta_airfoil_tools.py
    exit
)

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py manta_airfoil_tools.py
    exit
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python manta_airfoil_tools.py
    exit
)

echo.
echo ERROR: Python not found.
echo Please install Python and ensure it is in PATH.
pause
