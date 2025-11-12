@echo off
title GitHub Setup
color 0B

cd /d %~dp0

echo ========================================
echo   GitHub Repository Setup
echo ========================================
echo.

REM Check Git
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed
    echo.
    echo Download from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo Git is installed:
git --version
echo.

REM Get user info
echo Enter your GitHub account information:
echo.
set /p git_name="Your Name: "
set /p git_email="Your Email: "
echo.

REM Git 설정
echo [1/6] Git 사용자 정보 설정 중...
git config user.name "%git_name%"
git config user.email "%git_email%"
echo OK: 사용자 정보 설정 완료
echo.

REM Git 초기화
echo [2/6] Git 저장소 초기화 중...
if exist ".git" (
    echo WARNING: 이미 Git 저장소가 초기화되어 있습니다.
    echo.
) else (
    git init
    echo OK: Git 초기화 완료
    echo.
)

REM 파일 추가
echo [3/6] 파일 추가 중...
git add .
echo OK: 파일 추가 완료
echo.

REM 커밋
echo [4/6] 첫 커밋 생성 중...
git commit -m "Initial commit - Woori File Share V3"
if errorlevel 1 (
    echo WARNING: 커밋할 변경사항이 없습니다.
    echo.
)
echo.

REM 브랜치 이름 변경
echo [5/6] 메인 브랜치 설정 중...
git branch -M main
echo OK: main 브랜치로 설정 완료
echo.

REM 원격 저장소 설정
echo [6/6] GitHub 저장소 연결...
echo.
echo GitHub 저장소 URL을 입력하세요:
echo 예: https://github.com/myname/woori-fileshare.git
echo.
set /p repo_url="저장소 URL: "
echo.

git remote add origin "%repo_url%"
if errorlevel 1 (
    echo WARNING: 원격 저장소가 이미 설정되어 있을 수 있습니다.
    echo 기존 설정 제거 후 재설정:
    git remote remove origin
    git remote add origin "%repo_url%"
)
echo OK: 원격 저장소 연결 완료
echo.

echo ========================================
echo   초기 설정 완료!
echo ========================================
echo.
echo 다음 단계:
echo.
echo 1. GitHub에 업로드:
echo    git_upload.bat 실행 또는
echo    git push -u origin main
echo.
echo 2. GitHub Actions에서 자동 빌드 확인:
echo    %repo_url%/actions
echo.
echo 3. 5-10분 후 Artifacts에서 .dmg 다운로드
echo.
pause

REM 바로 푸시할지 물어보기
echo.
echo 지금 바로 GitHub에 업로드하시겠습니까? (y/n)
set /p do_push="> "

if /i "%do_push%"=="y" (
    echo.
    echo GitHub에 푸시 중...
    git push -u origin main
    
    if errorlevel 1 (
        echo.
        echo ERROR: 푸시 실패
        echo GitHub 로그인이 필요할 수 있습니다.
        echo.
        pause
    ) else (
        echo.
        echo ========================================
        echo   업로드 완료!
        echo ========================================
        echo.
        echo GitHub Actions에서 자동 빌드가 시작됩니다.
        echo %repo_url%/actions
        echo.
        pause
    )
) else (
    echo.
    echo 나중에 git_upload.bat을 실행하여 업로드하세요.
    echo.
    pause
)
