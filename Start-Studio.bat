@echo off
title NanoPro Reel Maker - RTX 3050 Studio
rem Auto-detect: switch to the folder this .bat file lives in (no hardcoded path)
cd /d "%~dp0"
echo ================================================================
echo   🎬 Starting NanoPro Reel Maker with NVIDIA RTX 3050 GPU...
echo ================================================================
timeout /t 2 >nul
start http://localhost:8501
python -m streamlit run app.py
