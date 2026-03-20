@echo off
REM Automated script to push all remaining files to GitHub
REM This script requires Git to be installed and available in PATH
REM Usage: Run this script after installing Git

setlocal enabledelayedexpansion
cd /d "d:\New folder (37)\YT\video_processor\video_processor"

echo ============================================
echo GitHub Push All Files Script
echo ============================================
echo.

REM Check if Git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b 1
)

echo Git is available!
echo.

REM Configure Git user if not already set globally
echo Setting Git configuration...
git config user.name "rufsanrafi4-design"
git config user.email "rufsanrafi4@gmail.com"

echo.
echo Staging all files...
git add .

echo.
echo Creating commit...
git commit -m "Add remaining project files - Pro Video Suite v9"

if errorlevel 1 (
    echo ERROR: Commit failed. Files may already be committed.
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
git push -u origin main

if errorlevel 1 (
    echo ERROR: Push failed. Check your GitHub credentials.
    pause
    exit /b 1
)

echo.
echo ============================================
echo SUCCESS! All files pushed to GitHub
echo ============================================
echo.
echo View your repository at:
echo https://github.com/rufsanrafi4-design/xgenSuite
echo.
pause
