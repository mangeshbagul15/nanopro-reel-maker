@echo off
setlocal
title NanoPro Reel Maker - Disable auto-start

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\NanoPro Studio.lnk"

if exist "%SHORTCUT%" (
  del "%SHORTCUT%"
  echo [OK] Auto-start disabled. The Local Studio will no longer start at logon.
) else (
  echo [i] Auto-start was not enabled.
)
echo.
echo     Note: a Studio that is running right now keeps running.
echo     Close it from Task Manager if needed (python / streamlit on port 8501).
echo.
pause
