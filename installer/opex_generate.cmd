@echo off
REM Wrapper for opex_generate.exe
REM Runs the executable from the same directory
"%~dp0opex_generate.exe" %*
EXIT /B %ERRORLEVEL%
