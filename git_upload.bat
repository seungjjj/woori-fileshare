@echo off
chcp 65001 >nul
title GitHub 업로드
color 0B

cd /d %~dp0

echo ========================================
echo   GitHub에 코드 업로드 (자동 빌드)
echo ========================================
echo.

REM Git 확인
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git이 설치되어 있지 않습니다.
    echo.
    echo https://git-scm.com/download/win 에서 다운로드하세요.
    echo.
    pause
    exit /b 1
)

REM 커밋 메시지 입력
set /p commit_msg="커밋 메시지 입력 (Enter=자동): "
if "%commit_msg%"=="" set commit_msg=Update code

echo.
echo [1/3] 파일 추가 중...
git add .
if errorlevel 1 (
    echo ERROR: git add 실패
    pause
    exit /b 1
)
echo OK: 파일 추가 완료
echo.

echo [2/3] 커밋 중...
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo WARNING: 변경사항이 없거나 커밋 실패
    echo.
)
echo.

echo [3/3] GitHub에 푸시 중...
git push
if errorlevel 1 (
    echo ERROR: git push 실패
    echo.
    echo 저장소가 설정되지 않았다면:
    echo git remote add origin https://github.com/[사용자명]/[저장소명].git
    echo git branch -M main
    echo git push -u origin main
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   업로드 완료!
echo ========================================
echo.
echo ✓ GitHub에 코드가 업로드되었습니다.
echo ✓ GitHub Actions가 자동으로 macOS 빌드를 시작합니다.
echo ✓ 5-10분 후 Artifacts에서 .dmg 다운로드 가능!
echo.
echo GitHub 저장소 Actions 탭을 확인하세요:
echo https://github.com/[사용자명]/[저장소명]/actions
echo.
pause
