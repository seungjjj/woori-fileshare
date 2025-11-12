#!/bin/bash
# macOS용 클라이언트 실행 스크립트

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   파일 공유 클라이언트 (macOS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 가상환경 확인
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}가상환경이 없습니다. 생성 중...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}가상환경 생성 완료${NC}"
    echo ""
fi

# 가상환경 활성화
echo -e "${BLUE}가상환경 활성화...${NC}"
source venv/bin/activate

# 의존성 확인
if ! python -c "import PyQt5" 2>/dev/null; then
    echo -e "${YELLOW}의존성 설치 중...${NC}"
    pip install -q -r requirements_macos.txt
    echo -e "${GREEN}의존성 설치 완료${NC}"
    echo ""
fi

# 클라이언트 실행
echo -e "${GREEN}클라이언트 시작...${NC}"
echo ""
python3 gui_client_pyqt.py

# 종료 시 가상환경 비활성화
deactivate
