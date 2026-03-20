@echo off
REM GitHub Repository Setup Script for Video Processor
REM This script will initialize git and push to GitHub

cd /d "d:\New folder (37)\YT\video_processor\video_processor"

REM Initialize git repository
git init

REM Configure git user
git config user.name "rufsanrafi4-design"
git config user.email "rufsanrafi4@gmail.com"

REM Add all files
git add .

REM Create initial commit
git commit -m "Initial commit - Pro Video Suite v9"

REM Add remote origin
git remote add origin https://github.com/rufsanrafi4-design/xgenSuite.git

REM Set main branch
git branch -M main

REM Push to GitHub
git push -u origin main

echo.
echo Setup complete! Your repository has been pushed to GitHub.
pause
