@echo off
REM Initialize git repository for GitHub Desktop
REM This creates the .git folder structure that GitHub Desktop recognizes

setlocal enabledelayedexpansion
cd /d "d:\New folder (37)\YT\video_processor\video_processor"

if not exist ".git" (
    mkdir .git
    mkdir .git\objects
    mkdir .git\refs
    mkdir .git\refs\heads
    mkdir .git\refs\tags
    
    echo Initializing Git repository...
)

REM Create HEAD file
(
    echo ref: refs/heads/main
) > .git\HEAD

REM Create config file
(
    echo [core]
    echo    repositoryformatversion = 0
    echo    filemode = false
    echo    bare = false
    echo    logallrefupdates = true
    echo    ignorecase = true
    echo [user]
    echo    name = rufsanrafi4-design
    echo    email = rufsanrafi4@gmail.com
    echo [remote "origin"]
    echo    url = https://github.com/rufsanrafi4-design/xgenSuite.git
    echo    fetch = +refs/heads/*:refs/remotes/origin/*
    echo [branch "main"]
    echo    remote = origin
    echo    merge = refs/heads/main
) > .git\config

REM Create description file
(
    echo Unnamed repository; edit this file 'description' to name the repository.
) > .git\description

echo.
echo Git repository initialized!
echo.
echo Next steps in GitHub Desktop:
echo 1. File -^> Add Local Repository
echo 2. Select: d:\New folder (37)\YT\video_processor\video_processor
echo 3. Commit message: Initial commit - Pro Video Suite v9
echo 4. Click "Commit to main"
echo 5. Click "Publish repository"
echo.
echo Your repo will be published to:
echo https://github.com/rufsanrafi4-design/video_processor
echo.
pause
