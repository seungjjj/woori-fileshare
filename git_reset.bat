@echo off
title Git Reset
color 0C
cd /d %~dp0

echo ========================================
echo   WARNING: Reset Git Repository
echo ========================================
echo.
echo This will DELETE all Git history!
echo.
echo Continue? (y/n)
set /p confirm="> "

if /i not "%confirm%"=="y" (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo Deleting .git folder...
if exist ".git" (
    rmdir /s /q ".git"
    echo OK: Git folder deleted
) else (
    echo No .git folder found
)

echo.
echo ========================================
echo   Git Reset Complete
echo ========================================
echo.
echo Now run: git_setup_simple.bat
echo.
pause
