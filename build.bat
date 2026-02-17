@echo off
echo Building %~dp0 ...
cd /d %~dp0

pyinstaller ^
    --onefile ^
    --noconsole ^
    --name WinServiceHelper ^
    --hidden-import win11toast ^
    --hidden-import pystray._win32 ^
    --paths src ^
    src\main.py

echo.
if exist dist\WinServiceHelper.exe (
    echo BUILD SUCCESSFUL: dist\WinServiceHelper.exe
) else (
    echo BUILD FAILED
)
pause
