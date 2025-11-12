#!/bin/bash
# macOS용 .app 파일 빌드 스크립트

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   macOS .app 파일 빌드${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}가상환경이 없습니다. 생성 중...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_macos.txt
    echo -e "${GREEN}가상환경 및 의존성 설치 완료${NC}"
    echo ""
else
    source venv/bin/activate
fi

# PyInstaller 확인
echo -e "${BLUE}[1/5] PyInstaller 확인 중...${NC}"
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}PyInstaller 설치 중...${NC}"
    pip install pyinstaller
fi
echo -e "${GREEN}OK: PyInstaller 준비 완료${NC}"
echo ""

# 이전 빌드 정리
echo -e "${BLUE}[2/5] 이전 빌드 정리 중...${NC}"
rm -rf dist/*.app
rm -rf build
echo -e "${GREEN}OK: 정리 완료${NC}"
echo ""

# 클라이언트 빌드
echo -e "${BLUE}[3/5] 클라이언트 빌드 중...${NC}"
echo ""
pyinstaller --clean build_client_mac.spec
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}OK: 클라이언트 빌드 완료${NC}"
else
    echo ""
    echo -e "${RED}ERROR: 클라이언트 빌드 실패${NC}"
    exit 1
fi
echo ""

# 서버 빌드
echo -e "${BLUE}[4/5] 서버 빌드 중...${NC}"
echo ""
pyinstaller --clean build_server_mac.spec
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}OK: 서버 빌드 완료${NC}"
else
    echo ""
    echo -e "${RED}ERROR: 서버 빌드 실패${NC}"
    exit 1
fi
echo ""

# 결과 확인
echo -e "${BLUE}[5/5] 빌드 결과 확인...${NC}"
echo ""

if [ -d "dist/Woori_Client.app" ]; then
    echo -e "${GREEN}✓ 클라이언트: dist/Woori_Client.app${NC}"
    CLIENT_SIZE=$(du -sh dist/Woori_Client.app | cut -f1)
    echo -e "  크기: ${CLIENT_SIZE}"
else
    echo -e "${RED}✗ 클라이언트: 빌드 파일 없음${NC}"
fi

echo ""

if [ -d "dist/Woori_Server.app" ]; then
    echo -e "${GREEN}✓ 서버: dist/Woori_Server.app${NC}"
    SERVER_SIZE=$(du -sh dist/Woori_Server.app | cut -f1)
    echo -e "  크기: ${SERVER_SIZE}"
else
    echo -e "${RED}✗ 서버: 빌드 파일 없음${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   빌드 완료!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}파일 위치: dist 폴더${NC}"
echo ""
echo -e "${YELLOW}사용 방법:${NC}"
echo -e "  1. Finder에서 dist 폴더 열기"
echo -e "  2. .app 파일 더블클릭하여 실행"
echo -e "  3. 보안 경고 시 '시스템 환경설정 → 보안' 에서 허용"
echo ""
echo -e "${YELLOW}배포용 .dmg 파일 만들기:${NC}"
echo -e "  ./create_dmg.sh"
echo -e "  → 일반 프로그램처럼 설치 가능한 .dmg 파일 생성"
echo ""

# 가상환경 비활성화
deactivate

# .dmg 생성 제안
echo -e "${BLUE}.dmg 설치 파일을 만드시겠습니까? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    ./create_dmg.sh
else
    # dist 폴더 열기
    echo -e "${BLUE}dist 폴더를 여시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        open dist
    fi
fi
