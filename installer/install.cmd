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

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

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
if exist "%SCRIPT_DIR%\bin\opex_generate.exe" (
    xcopy /Y "%SCRIPT_DIR%\bin\opex_generate.exe" "!BIN_DIR!\" >nul
) else (
    echo ERROR: Cannot find opex_generate.exe at %SCRIPT_DIR%\bin\opex_generate.exe
    pause
    exit /b 1
)

if exist "%SCRIPT_DIR%\bin\opex_generate.cmd" (
    xcopy /Y "%SCRIPT_DIR%\bin\opex_generate.cmd" "!BIN_DIR!\" >nul
) else (
    echo ERROR: Cannot find opex_generate.cmd at %SCRIPT_DIR%\bin\opex_generate.cmd
    pause
    exit /b 1
)

if exist "%SCRIPT_DIR%\README.txt" (
    xcopy /Y "%SCRIPT_DIR%\README.txt" "!INSTALL_DIR!\" >nul
) else (
    echo WARNING: Cannot find README.txt
)

if exist "%SCRIPT_DIR%\LICENSE.md" (
    xcopy /Y "%SCRIPT_DIR%\LICENSE.md" "!INSTALL_DIR!\" >nul
) else (
    echo WARNING: Cannot find LICENSE.md
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
