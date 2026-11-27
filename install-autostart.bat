@echo off
setlocal
title NanoPro Reel Maker - Enable auto-start
cd /d "%~dp0"

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\NanoPro Studio.lnk"

echo ================================================================
echo    Enable auto-start of the Local Studio
echo    Folder: %CD%
echo ================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "$lnk = $ws.CreateShortcut('%SHORTCUT%');" ^
  "$lnk.TargetPath = 'wscript.exe';" ^
  "$lnk.Arguments = '\"%~dp0Start-Studio-Background.vbs\"';" ^
  "$lnk.WorkingDirectory = '%~dp0';" ^
  "$lnk.WindowStyle = 7;" ^
  "$lnk.Description = 'NanoPro Reel Maker - Local Studio (auto-start)';" ^
  "$lnk.Save();"

if exist "%SHORTCUT%" (
  echo [OK] Auto-start enabled.
  echo      The Local Studio will now start automatically every time you log in.
  echo      The "Switch to Local" button will work any time - no manual start needed.
  echo.
  echo      To start it right now without logging out, double-click
  echo      Start-Studio-Background.vbs
) else (
  echo [ERROR] Could not create the startup shortcut.
)
echo.
pause
