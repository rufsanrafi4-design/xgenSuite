@echo off
title Pro Video Processor — Launcher
cd /d "%~dp0"

echo ============================================================
echo   PRO VIDEO PROCESSOR — One-Click Launcher
echo ============================================================
echo.

:: ── Check Python ──
set PYTHON_CMD=python
if exist "%~dp0python_portable\python\python.exe" (
    echo [OK] Portable Python found. Using embedded version.
    set PYTHON_CMD="%~dp0python_portable\python\python.exe"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [X] Python not found!
        echo     Please install Python 3.x from https://python.org
        echo     Make sure to check "Add Python to PATH" during install.
        echo.
        pause
        exit /b 1
    )
    echo [OK] System Python found.
)

:: ── Install pip dependencies (first run only) ──
echo [*] Checking dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt --quiet >nul 2>&1
echo [OK] Dependencies ready.

:: ── Check FFmpeg ──
if exist "ffmpeg_bin\ffmpeg.exe" (
    echo [OK] FFmpeg found in ffmpeg_bin\.
) else (
    where ffmpeg >nul 2>&1
    if errorlevel 1 (
        echo [!] FFmpeg not found!
        echo     Please run setup.bat first, or manually place
        echo     ffmpeg.exe and ffprobe.exe in the ffmpeg_bin\ folder.
        echo.
        pause
        exit /b 1
    )
    echo [OK] FFmpeg found in PATH.
)

:: ── Launch the App ──
echo.
echo ============================================================
echo   Launching Pro Video Processor...
echo ============================================================
echo.
%PYTHON_CMD% app.py

if errorlevel 1 (
    echo.
    echo [!] App exited with an error. Check the output above.
    pause
)
