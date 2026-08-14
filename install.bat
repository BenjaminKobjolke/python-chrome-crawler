@echo off
uv sync
if errorlevel 1 exit /b 1
call "%~dp0tools\update_extensions.bat"
