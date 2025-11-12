#!/bin/bash
# macOS용 초기 설정 스크립트

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
echo -e "${BLUE}   Woori 파일 공유 프로그램${NC}"
echo -e "${BLUE}   macOS 초기 설정${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Python 확인
echo -e "${BLUE}[1/5] Python 확인 중...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3가 설치되어 있지 않습니다.${NC}"
    echo ""
    echo -e "${YELLOW}설치 방법:${NC}"
    echo "  1. https://www.python.org/downloads/ 에서 Python 다운로드"
    echo "  또는"
    echo "  2. Homebrew 사용: brew install python@3.11"
    echo ""
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}OK: ${PYTHON_VERSION} 발견${NC}"
fi
echo ""

# 가상환경 생성
echo -e "${BLUE}[2/5] 가상환경 생성 중...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}가상환경이 이미 존재합니다. 재생성하시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}OK: 가상환경 재생성 완료${NC}"
    else
        echo -e "${YELLOW}기존 가상환경 사용${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}OK: 가상환경 생성 완료${NC}"
fi
echo ""

# 가상환경 활성화
echo -e "${BLUE}[3/5] 가상환경 활성화...${NC}"
source venv/bin/activate
echo -e "${GREEN}OK: 가상환경 활성화됨${NC}"
echo ""

# pip 업그레이드
echo -e "${BLUE}[4/5] pip 업그레이드 중...${NC}"
pip install --upgrade pip --quiet
echo -e "${GREEN}OK: pip 업그레이드 완료${NC}"
echo ""

# 의존성 설치
echo -e "${BLUE}[5/5] 의존성 패키지 설치 중...${NC}"
echo -e "${YELLOW}이 작업은 몇 분 소요될 수 있습니다...${NC}"
echo ""

if [ -f "requirements_macos.txt" ]; then
    pip install -r requirements_macos.txt
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}OK: 모든 패키지 설치 완료${NC}"
    else
        echo ""
        echo -e "${RED}ERROR: 패키지 설치 중 오류 발생${NC}"
        echo -e "${YELLOW}수동 설치를 시도하세요:${NC}"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements_macos.txt"
        deactivate
        exit 1
    fi
else
    echo -e "${RED}ERROR: requirements_macos.txt 파일이 없습니다.${NC}"
    deactivate
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   설정 완료!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 실행 권한 부여
echo -e "${BLUE}실행 스크립트에 권한 부여 중...${NC}"
chmod +x run_server_mac.sh
chmod +x run_client_mac.sh
chmod +x build_mac_apps.sh
chmod +x create_dmg.sh
chmod +x build_all_mac.sh
echo -e "${GREEN}OK: 권한 부여 완료${NC}"
echo ""

echo -e "${GREEN}✓ 모든 설정이 완료되었습니다!${NC}"
echo ""
echo -e "${YELLOW}사용 방법:${NC}"
echo ""
echo -e "  ${BLUE}서버 실행:${NC}"
echo -e "    ./run_server_mac.sh"
echo ""
echo -e "  ${BLUE}클라이언트 실행:${NC}"
echo -e "    ./run_client_mac.sh"
echo ""
echo -e "  ${BLUE}.app + .dmg 파일 빌드 (통합):${NC}"
echo -e "    ./build_all_mac.sh"
echo ""
echo -e "  ${BLUE}.app 파일만 빌드:${NC}"
echo -e "    ./build_mac_apps.sh"
echo ""
echo -e "${YELLOW}참고:${NC}"
echo -e "  - 가상환경: ${PWD}/venv"
echo -e "  - 가이드: MacOS_Setup_Guide.md"
echo ""

# 가상환경 비활성화
deactivate

echo -e "${BLUE}지금 서버를 실행하시겠습니까? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    ./run_server_mac.sh
fi
