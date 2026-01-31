@echo off
REM Installer for Opex Manifest Generator - Requires Administrator privileges

REM Check for administrator privileges
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo This installer requires Administrator privileges.
    echo Please right-click install.cmd and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Validate portable layout
IF NOT EXIST "%~dp0bin\opex_generate.exe" (
    echo ERROR: Could not find bin\opex_generate.exe
    echo Please run install.cmd from the root of the portable package.
    pause
    exit /b 1
)

echo Installing to: %ProgramFiles%\Opex Generate
SET INSTALL_TO=%ProgramFiles%\Opex Generate
echo.
echo Copying files...

REM Create destination directory
IF NOT EXIST "%INSTALL_TO%" mkdir "%INSTALL_TO%"

REM Copy files using xcopy
xcopy "%~dp0*" "%INSTALL_TO%\" /E /I /H /Y /Q
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Installation failed (xcopy exit code: %ERRORLEVEL%)
    pause
    exit /b 1
)

echo.
echo Installation complete!
echo Installed to: %INSTALL_TO%
echo.
echo You can now run: "%INSTALL_TO%\bin\opex_generate.cmd"
echo.
pause
EXIT /B 0
