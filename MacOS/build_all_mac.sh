#!/bin/bash
# macOS용 전체 빌드 스크립트 (Windows build_pyqt_all.bat과 동일)
# .app 파일 생성 → .dmg 설치 파일 생성까지 한 번에 처리

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

clear
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   macOS 전체 빌드 (통합 스크립트)     ${NC}"
echo -e "${BLUE}   .app → .dmg 자동 생성                ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}가상환경이 없습니다. 생성 중...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -r requirements_macos.txt
    echo -e "${GREEN}가상환경 및 의존성 설치 완료${NC}"
    echo ""
else
    source venv/bin/activate
fi

# PyInstaller 확인
echo -e "${BLUE}[1/6] PyInstaller 확인 중...${NC}"
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}PyInstaller 설치 중...${NC}"
    pip install pyinstaller --quiet
fi
echo -e "${GREEN}OK: PyInstaller 준비 완료${NC}"
echo ""

# 이전 빌드 정리
echo -e "${BLUE}[2/6] 이전 빌드 정리 중...${NC}"
rm -rf dist/*.app
rm -rf dist/*.dmg
rm -rf build
echo -e "${GREEN}OK: 정리 완료${NC}"
echo ""

# 필요한 리소스 동기화 (CI 환경 대비)
echo -e "${BLUE}필요 파일 동기화 중...${NC}"
# 클라이언트 설정
if [ ! -f "client_settings_pyqt.json" ] && [ -f "../client_settings_pyqt.json" ]; then
    cp "../client_settings_pyqt.json" "./client_settings_pyqt.json"
fi
# 서버 설정
if [ ! -f "unified_server_config_pyqt.json" ] && [ -f "../unified_server_config_pyqt.json" ]; then
    cp "../unified_server_config_pyqt.json" "./unified_server_config_pyqt.json"
fi
# Flask 템플릿 폴더
if [ -d "../templates" ] && [ ! -d "./templates" ]; then
    cp -R "../templates" "./templates"
fi
echo -e "${GREEN}OK: 동기화 완료${NC}"
echo ""

# 클라이언트 빌드
echo -e "${BLUE}[3/6] 클라이언트 .app 빌드 중...${NC}"
echo -e "${YELLOW}(시간이 걸릴 수 있습니다...)${NC}"
echo ""
pyinstaller --clean build_client_mac.spec 2>&1 | grep -E "(Building|Completed|ERROR|WARNING)" || true
if [ ${PIPESTATUS[0]} -eq 0 ] && [ -d "dist/Woori_Client.app" ]; then
    echo ""
    echo -e "${GREEN}OK: 클라이언트 빌드 완료${NC}"
    CLIENT_SIZE=$(du -sh dist/Woori_Client.app | cut -f1)
    echo -e "  크기: ${CLIENT_SIZE}"
else
    echo ""
    echo -e "${RED}ERROR: 클라이언트 빌드 실패${NC}"
    deactivate
    exit 1
fi
echo ""

# 서버 빌드
echo -e "${BLUE}[4/6] 서버 .app 빌드 중...${NC}"
echo -e "${YELLOW}(시간이 걸릴 수 있습니다...)${NC}"
echo ""
pyinstaller --clean build_server_mac.spec 2>&1 | grep -E "(Building|Completed|ERROR|WARNING)" || true
if [ ${PIPESTATUS[0]} -eq 0 ] && [ -d "dist/Woori_Server.app" ]; then
    echo ""
    echo -e "${GREEN}OK: 서버 빌드 완료${NC}"
    SERVER_SIZE=$(du -sh dist/Woori_Server.app | cut -f1)
    echo -e "  크기: ${SERVER_SIZE}"
else
    echo ""
    echo -e "${RED}ERROR: 서버 빌드 실패${NC}"
    deactivate
    exit 1
fi
echo ""

# .dmg 생성 준비
echo -e "${BLUE}[5/6] .dmg 설치 파일 생성 중...${NC}"
DMG_NAME="Woori_파일공유_V3"
TEMP_DMG_DIR="dmg_temp"
rm -rf "${TEMP_DMG_DIR}"
mkdir -p "${TEMP_DMG_DIR}"

# .app 파일 복사
cp -R "dist/Woori_Server.app" "${TEMP_DMG_DIR}/"
cp -R "dist/Woori_Client.app" "${TEMP_DMG_DIR}/"

# 가이드 문서 복사
if [ -f "📘_먼저_읽어주세요_MacOS.txt" ]; then
    cp "📘_먼저_읽어주세요_MacOS.txt" "${TEMP_DMG_DIR}/📘_사용방법.txt"
fi
if [ -f "빠른시작_MacOS.txt" ]; then
    cp "빠른시작_MacOS.txt" "${TEMP_DMG_DIR}/"
fi

# Applications 심볼릭 링크 생성
ln -s /Applications "${TEMP_DMG_DIR}/Applications"

# .dmg 파일 생성
rm -f "dist/${DMG_NAME}.dmg"
hdiutil create -volname "${DMG_NAME}" \
    -srcfolder "${TEMP_DMG_DIR}" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}.dmg" > /dev/null 2>&1

if [ $? -eq 0 ] && [ -f "dist/${DMG_NAME}.dmg" ]; then
    echo -e "${GREEN}OK: .dmg 파일 생성 완료${NC}"
    DMG_SIZE=$(du -sh "dist/${DMG_NAME}.dmg" | cut -f1)
    echo -e "  크기: ${DMG_SIZE}"
else
    echo -e "${RED}ERROR: .dmg 파일 생성 실패${NC}"
    rm -rf "${TEMP_DMG_DIR}"
    deactivate
    exit 1
fi

# 정리
rm -rf "${TEMP_DMG_DIR}"
echo ""

# 빌드 정리
echo -e "${BLUE}[6/6] 빌드 정리 중...${NC}"
rm -rf build
echo -e "${GREEN}OK: 정리 완료${NC}"
echo ""

# 최종 결과
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   전체 빌드 완료!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✓ 생성된 파일:${NC}"
echo ""
echo -e "  📦 dist/Woori_파일공유_V3.dmg"
echo -e "     크기: ${DMG_SIZE}"
echo -e "     → 배포용 설치 파일"
echo ""
echo -e "  📱 dist/Woori_Client.app"
echo -e "     크기: ${CLIENT_SIZE}"
echo ""
echo -e "  📱 dist/Woori_Server.app"
echo -e "     크기: ${SERVER_SIZE}"
echo ""
echo -e "${YELLOW}사용 방법:${NC}"
echo -e "  1. .dmg 파일을 배포하세요"
echo -e "  2. 받는 사람은 .dmg 더블클릭 → 드래그 → 설치"
echo -e "  3. Launchpad에서 Woori 검색하여 실행"
echo ""
echo -e "${YELLOW}개발/테스트용:${NC}"
echo -e "  • dist 폴더의 .app 파일 직접 실행 가능"
echo ""

# 가상환경 비활성화
deactivate

# dist 폴더 열기
echo -e "${BLUE}dist 폴더를 여시겠습니까? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    open dist
fi

echo ""
echo -e "${GREEN}🎉 빌드 완료! 파일을 배포하세요!${NC}"
