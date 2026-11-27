@echo off
setlocal
title NanoPro Reel Maker - Local RTX Studio
rem ------------------------------------------------------------------
rem  NanoPro Reel Maker - Local Studio launcher (Windows)
rem   - runs from this folder (no hardcoded paths)
rem   - installs / updates the Python dependencies automatically
rem   - starts the Studio on http://localhost:8501
rem   - opens the browser only AFTER the server is actually ready
rem   - keeps this window open on error so the message is readable
rem ------------------------------------------------------------------
cd /d "%~dp0"

echo ================================================================
echo    NanoPro Reel Maker - Local RTX Studio
echo    Folder: %CD%
echo ================================================================
echo.

rem --- 1) Verify a real Python interpreter is available --------------
where python >nul 2>nul
if errorlevel 1 goto :no_python
python -c "import sys" >nul 2>nul
if errorlevel 1 goto :no_python

rem --- 2) Install / update dependencies into THIS Python -------------
echo [1/3] Installing / checking dependencies (the first run can take a few minutes)...
python -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :pip_failed

python -c "import streamlit" >nul 2>nul
if errorlevel 1 goto :pip_failed

rem --- 3) Free port 8501 if an old Studio is still running -----------
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo [i] Stopping a previous Studio still using port 8501 PID %%p ...
    taskkill /f /pid %%p >nul 2>nul
)

echo [2/3] Starting the Studio server on http://localhost:8501 ...
echo        Keep this window open while you use the Studio. Press Ctrl+C to stop.
echo.

rem --- 4) Open the browser once the server answers (max ~60s) --------
start "" powershell -NoProfile -WindowStyle Hidden -Command "for($i=0;$i -lt 60;$i++){try{(Invoke-WebRequest -UseBasicParsing 'http://localhost:8501' -TimeoutSec 1)|Out-Null;Start-Process 'http://localhost:8501';break}catch{Start-Sleep -Seconds 1}}"

rem --- 5) Run Streamlit (blocks until you press Ctrl+C) --------------
python -m streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false

set EXITCODE=%errorlevel%
echo.
echo [3/3] Studio stopped (exit code %EXITCODE%).
echo        If the browser said "can't be reached", copy the error above.
echo.
pause
exit /b %EXITCODE%

:no_python
echo.
echo [ERROR] A working Python interpreter was not found.
echo         1. Install Python 3.10+ from https://www.python.org/downloads/
echo         2. During setup tick "Add python.exe to PATH".
echo         3. Close this window, then double-click Start-Studio.bat again.
echo.
pause
exit /b 1

:pip_failed
echo.
echo [ERROR] Could not install the required Python packages.
echo         Check your internet connection and the messages above, then retry.
echo.
pause
exit /b 1
