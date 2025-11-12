@echo off
title PyQt5 Client Test
color 0B

cd /d %~dp0

echo ========================================
echo   PyQt5 Modern Client Test
echo ========================================
echo.
echo Installing PyQt5 if needed...
E:\remote-file-share\venv\Scripts\pip.exe install PyQt5 -q
echo.
echo Starting PyQt5 client...
echo.

E:\remote-file-share\venv\Scripts\python.exe gui_client_pyqt.py

pause
