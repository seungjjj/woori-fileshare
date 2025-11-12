@echo off
title PyQt5 Build
color 0B

cd /d %~dp0

echo ========================================
echo   PyQt5 Client and Server Build
echo ========================================
echo.

REM Install PyInstaller
echo [1/5] Installing PyInstaller...
E:\remote-file-share\venv\Scripts\pip.exe install pyinstaller -q
if errorlevel 1 (
    echo ERROR: PyInstaller installation failed
    pause
    exit /b 1
)
echo OK: PyInstaller ready
echo.

REM Clean previous builds
echo [2/5] Cleaning previous builds...
if exist "dist\Woori_Client_PyQt.exe" del /q "dist\Woori_Client_PyQt.exe"
if exist "dist\Woori_Server_PyQt.exe" del /q "dist\Woori_Server_PyQt.exe"
if exist "build" rmdir /s /q "build"
echo OK: Cleanup complete
echo.

REM Build client
echo [3/5] Building client...
echo.
E:\remote-file-share\venv\Scripts\pyinstaller.exe --clean build_client_pyqt.spec
if errorlevel 1 (
    echo ERROR: Client build failed
    pause
    exit /b 1
)
echo.
echo OK: Client build complete
echo.

REM Build server
echo [4/5] Building server...
echo.
E:\remote-file-share\venv\Scripts\pyinstaller.exe --clean build_server_pyqt.spec
if errorlevel 1 (
    echo ERROR: Server build failed
    pause
    exit /b 1
)
echo.
echo OK: Server build complete
echo.

REM Check results
echo [5/5] Checking build results...
echo.
if exist "dist\Woori_Client_PyQt.exe" (
    echo OK: Client - dist\Woori_Client_PyQt.exe
) else (
    echo ERROR: Client build file not found
)

if exist "dist\Woori_Server_PyQt.exe" (
    echo OK: Server - dist\Woori_Server_PyQt.exe
) else (
    echo ERROR: Server build file not found
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo Files location: dist folder
echo.

pause
