@echo off
REM Opex Manifest Generator Windows Installer
REM This script installs the Opex Manifest Generator to the Program Files directory

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo Opex Manifest Generator Installation
echo ===============================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

REM Define installation paths
set INSTALL_DIR=%LOCALAPPDATA%\Opex Manifest Generator
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
%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -Command "$path = [Environment]::GetEnvironmentVariable('Path', 'User'); if ($path -notlike '*%LOCALAPPDATA%\Opex Manifest Generator\bin*') { [Environment]::SetEnvironmentVariable('Path', $path + ';%LOCALAPPDATA%\Opex Manifest Generator\bin', 'User'); Write-Host 'Added to PATH' } else { Write-Host 'Already in PATH' }"

echo.
echo ===============================================
echo Installation Complete!
echo ===============================================
echo.
echo You can now use 'opex_generate' from the command line.
echo Note: You may need to restart your command prompt for PATH changes to take effect.
echo.
echo To get started, type: opex_generate --help
echo.
pause
