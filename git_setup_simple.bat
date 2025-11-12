@echo off
title GitHub Setup
color 0B
cd /d %~dp0

echo ========================================
echo   GitHub Repository Setup
echo ========================================
echo.

where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed
    echo Download: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Git version:
git --version
echo.

echo Enter GitHub account info:
set /p git_name="Name: "
set /p git_email="Email: "
echo.

echo [1/6] Configure Git user...
git config user.name "%git_name%"
git config user.email "%git_email%"
echo OK
echo.

echo [2/6] Initialize Git repository...
if exist ".git" (
    echo Already initialized
) else (
    git init
    echo OK
)
echo.

echo [3/6] Add files...
git add .
echo OK
echo.

echo [4/6] Create first commit...
git commit -m "Initial commit - Woori File Share V3"
echo.

echo [5/6] Set main branch...
git branch -M main
echo OK
echo.

echo [6/6] Connect to GitHub...
echo.
echo Enter GitHub repository URL:
echo Example: https://github.com/username/repo.git
set /p repo_url="URL: "
echo.

git remote remove origin >nul 2>&1
git remote add origin "%repo_url%"
echo OK
echo.

echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next: Push to GitHub? (y/n)
set /p do_push="> "

if /i "%do_push%"=="y" (
    echo.
    echo Pushing to GitHub...
    git push -u origin main
    echo.
    if errorlevel 1 (
        echo ERROR: Push failed
        pause
    ) else (
        echo SUCCESS!
        echo Check: %repo_url%/actions
        pause
    )
) else (
    echo.
    echo Run git_upload.bat later to push
    pause
)
