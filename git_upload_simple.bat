@echo off
title GitHub Upload
color 0B
cd /d %~dp0

echo ========================================
echo   Upload to GitHub
echo ========================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not installed
    echo Download: https://git-scm.com/download/win
    pause
    exit /b 1
)

set /p commit_msg="Commit message (Enter=Update): "
if "%commit_msg%"=="" set commit_msg=Update code

echo.
echo [1/3] Adding files...
git add .
if errorlevel 1 (
    echo ERROR: git add failed
    pause
    exit /b 1
)
echo OK
echo.

echo [2/3] Committing...
git commit -m "%commit_msg%"
echo.

echo [3/3] Pushing to GitHub...
git push
if errorlevel 1 (
    echo ERROR: git push failed
    echo.
    echo First time? Run: git_setup_simple.bat
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Upload Complete!
echo ========================================
echo.
echo GitHub Actions will build macOS .dmg
echo Check: GitHub repository - Actions tab
echo Download .dmg from Artifacts (5-10 min)
echo.
pause
