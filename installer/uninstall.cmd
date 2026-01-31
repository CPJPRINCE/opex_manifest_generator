@echo off
REM Uninstaller for Opex Manifest Generator
REM Removes installed files from Program Files or LocalAppData
SETLOCAL ENABLEDELAYEDEXPANSION

REM Detect admin rights to determine install location
NET SESSION >nul 2>&1
IF %ERRORLEVEL%==0 (
    SET DEST=%ProgramFiles%\Opex Generate
) ELSE (
    SET DEST=%LocalAppData%\Opex Generate
)

IF NOT EXIST "%DEST%" (
    echo Opex Generate is not installed at: %DEST%
    echo Nothing to uninstall.
    pause
    exit /b 0
)

echo This will remove Opex Generate from:
echo   %DEST%
echo.
SET /P CONFIRM=Are you sure? [Y/N]: 
IF /I NOT "%CONFIRM%"=="Y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Removing installation...
RD /S /Q "%DEST%"
IF %ERRORLEVEL%==0 (
    echo.
    echo Uninstall complete!
) ELSE (
    echo.
    echo ERROR: Failed to remove directory. Try running as Administrator.
    pause
    exit /b 1
)

echo.
pause
EXIT /B 0
