@echo off
setlocal
rem ------------------------------------------------------------------
rem  NanoPro Reel Maker - background Studio server (used by auto-start)
rem   - starts the Studio silently (no browser, no visible window)
rem   - used by Start-Studio-Background.vbs / the Windows login shortcut
rem   - logs to %TEMP%\nanopro_studio.log for troubleshooting
rem ------------------------------------------------------------------
cd /d "%~dp0"

set "LOG=%TEMP%\nanopro_studio.log"

rem --- If a Studio is already listening on 8501, do nothing ----------
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
    echo [%date% %time%] Studio already running on port 8501 ^(PID %%p^). >> "%LOG%"
    exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
    echo [%date% %time%] ERROR: Python not found on PATH. >> "%LOG%"
    exit /b 1
)

rem --- Install dependencies only when streamlit is missing -----------
python -c "import streamlit" >nul 2>nul
if errorlevel 1 (
    echo [%date% %time%] Installing dependencies... >> "%LOG%"
    python -m pip install --disable-pip-version-check -r requirements.txt >> "%LOG%" 2>&1
)

echo [%date% %time%] Starting Studio on http://localhost:8501 ... >> "%LOG%"
python -m streamlit run app.py --server.port 8501 --server.headless true --server.enableCORS false >> "%LOG%" 2>&1
exit /b 0
