@echo off
REM Opex Manifest Generator Windows Uninstaller
REM This script removes the Opex Manifest Generator from the system

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo Opex Manifest Generator Uninstallation
echo ===============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This uninstaller must be run as Administrator.
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Define installation directory
set INSTALL_DIR=%ProgramFiles%\Opex Manifest Generator
set BIN_DIR=!INSTALL_DIR!\bin

REM Confirm uninstallation
echo This will remove Opex Manifest Generator from:
echo !INSTALL_DIR!
echo.
set /p CONFIRM="Are you sure you want to uninstall? (Y/N): "
if /i not "!CONFIRM!"=="Y" (
    echo Uninstallation cancelled
    pause
    exit /b 0
)

REM Remove from PATH
echo Removing from PATH...
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do (
    set "OLD_PATH=%%B"
)

if not "!OLD_PATH!"=="" (
    REM Remove the bin directory from PATH
    setlocal enabledelayedexpansion
    set "NEW_PATH=!OLD_PATH:!BIN_DIR!=!"
    set "NEW_PATH=!NEW_PATH:;;=;!"

    if not "!NEW_PATH!"=="!OLD_PATH!" (
        setx /M PATH "!NEW_PATH!"
        echo Removed from PATH
    )
)

REM Remove installation directory
if exist "!INSTALL_DIR!" (
    echo Removing installation directory...
    rmdir /S /Q "!INSTALL_DIR!"
)

echo.
echo ===============================================
echo Uninstallation Complete!
echo ===============================================
echo.
pause
