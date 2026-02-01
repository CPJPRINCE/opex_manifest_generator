@echo off
REM Opex Manifest Generator Windows Installer
REM This script installs the Opex Manifest Generator to the Program Files directory

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo Opex Manifest Generator Installation
echo ===============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This installer must be run as Administrator.
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Define installation paths
set INSTALL_DIR=%ProgramFiles%\Opex Manifest Generator
set BIN_DIR=!INSTALL_DIR!\bin

echo Installing to: !INSTALL_DIR!
echo.

REM Create installation directory
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
    echo Created installation directory
)

if not exist "!BIN_DIR!" (
    mkdir "!BIN_DIR!"
    echo Created bin directory
)

REM Copy executable and wrapper
echo Copying files...
xcopy /Y "bin\opex_generate.exe" "!BIN_DIR!\" >nul
xcopy /Y "bin\opex_generate.cmd" "!BIN_DIR!\" >nul
xcopy /Y "README.txt" "!INSTALL_DIR!\" >nul
xcopy /Y "LICENSE.md" "!INSTALL_DIR!\" >nul 2>nul

if errorlevel 1 (
    echo ERROR: Failed to copy installation files
    pause
    exit /b 1
)

REM Add to PATH
echo Adding to PATH...
for /f "tokens=2*" %%A in ('reg query "HKLM\System\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do (
    set "OLD_PATH=%%B"
)

if not "!OLD_PATH!"=="" (
    echo !OLD_PATH! | find /I "!BIN_DIR!" >nul
    if errorlevel 1 (
        setx /M PATH "!OLD_PATH!;!BIN_DIR!"
        echo Added !BIN_DIR! to PATH
    ) else (
        echo Already in PATH
    )
) else (
    setx /M PATH "!BIN_DIR!"
)

echo.
echo ===============================================
echo Installation Complete!
echo ===============================================
echo.
echo You can now use 'opex_generate' from the command line.
echo.
echo To get started, type: opex_generate --help
echo.
pause
