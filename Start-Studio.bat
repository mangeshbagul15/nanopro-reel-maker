@echo off
title NanoPro Reel Maker - RTX 3050 Studio
cd /d "C:\Users\Mangesh\.gemini\antigravity\scratch\nanopro-reel-maker"
echo ================================================================
echo   🎬 Starting NanoPro Reel Maker with NVIDIA RTX 3050 GPU...
echo ================================================================
timeout /t 2 >nul
start http://localhost:8501
streamlit run app.py
