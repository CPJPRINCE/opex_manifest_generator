@echo off
REM Opex Manifest Generator Wrapper Script
REM This script sets up the environment and runs the opex_generate executable

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Run the executable with all passed arguments
"%SCRIPT_DIR%opex_generate.exe" %*

REM Exit with the same code as the executable
exit /b %errorlevel%
