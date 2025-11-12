@echo off
title PyQt5 Server Test
color 0B

cd /d %~dp0

echo ========================================
echo   PyQt5 Modern Server Test
echo ========================================
echo.
echo Installing PyQt5 if needed...
E:\remote-file-share\venv\Scripts\pip.exe install PyQt5 -q
echo.
echo Starting PyQt5 server...
echo.

start "" E:\remote-file-share\venv\Scripts\pythonw.exe unified_server_pyqt.py

echo 서버가 백그라운드에서 실행됩니다.
echo 시스템 트레이 아이콘을 확인하세요.
timeout /t 3 /nobreak >nul
