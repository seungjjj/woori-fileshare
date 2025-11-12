#!/bin/bash
# macOS용 .dmg 설치 파일 생성 스크립트

# 스크립트 위치로 이동
cd "$(dirname "$0")"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   .dmg 설치 파일 생성${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# .app 파일 존재 확인
if [ ! -d "dist/Woori_Server.app" ] || [ ! -d "dist/Woori_Client.app" ]; then
    echo -e "${YELLOW}.app 파일이 없습니다. 먼저 빌드를 진행합니다...${NC}"
    echo ""
    ./build_mac_apps.sh
    echo ""
fi

# .dmg 생성 폴더 준비
echo -e "${BLUE}[1/4] 준비 중...${NC}"
DMG_NAME="Woori_파일공유_V3"
TEMP_DMG_DIR="dmg_temp"
rm -rf "${TEMP_DMG_DIR}"
mkdir -p "${TEMP_DMG_DIR}"
echo -e "${GREEN}OK${NC}"
echo ""

# .app 파일 복사
echo -e "${BLUE}[2/4] 파일 복사 중...${NC}"
cp -R "dist/Woori_Server.app" "${TEMP_DMG_DIR}/"
cp -R "dist/Woori_Client.app" "${TEMP_DMG_DIR}/"

# 가이드 문서 복사
if [ -f "📘_먼저_읽어주세요_MacOS.txt" ]; then
    cp "📘_먼저_읽어주세요_MacOS.txt" "${TEMP_DMG_DIR}/📘_사용방법.txt"
fi
if [ -f "빠른시작_MacOS.txt" ]; then
    cp "빠른시작_MacOS.txt" "${TEMP_DMG_DIR}/"
fi

# Applications 심볼릭 링크 생성 (드래그 앤 드롭 설치용)
ln -s /Applications "${TEMP_DMG_DIR}/Applications"

echo -e "${GREEN}OK${NC}"
echo ""

# .dmg 파일 생성
echo -e "${BLUE}[3/4] .dmg 파일 생성 중...${NC}"
rm -f "dist/${DMG_NAME}.dmg"

# hdiutil을 사용하여 .dmg 생성
hdiutil create -volname "${DMG_NAME}" \
    -srcfolder "${TEMP_DMG_DIR}" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}.dmg"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}OK: .dmg 파일 생성 완료${NC}"
else
    echo ""
    echo -e "${RED}ERROR: .dmg 파일 생성 실패${NC}"
    rm -rf "${TEMP_DMG_DIR}"
    exit 1
fi
echo ""

# 정리
echo -e "${BLUE}[4/4] 정리 중...${NC}"
rm -rf "${TEMP_DMG_DIR}"
echo -e "${GREEN}OK${NC}"
echo ""

# 결과 확인
if [ -f "dist/${DMG_NAME}.dmg" ]; then
    DMG_SIZE=$(du -sh "dist/${DMG_NAME}.dmg" | cut -f1)
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}   .dmg 파일 생성 완료!${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "${GREEN}✓ 파일: dist/${DMG_NAME}.dmg${NC}"
    echo -e "  크기: ${DMG_SIZE}"
    echo ""
    echo -e "${YELLOW}사용 방법:${NC}"
    echo -e "  1. .dmg 파일 더블클릭"
    echo -e "  2. 앱을 Applications 폴더로 드래그"
    echo -e "  3. Launchpad에서 실행"
    echo ""
    echo -e "${YELLOW}배포:${NC}"
    echo -e "  • 이 .dmg 파일만 공유하면 됩니다"
    echo -e "  • 받는 사람은 설치 후 바로 사용 가능"
    echo ""
    
    # Finder에서 열기 제안
    echo -e "${BLUE}dist 폴더를 여시겠습니까? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        open dist
    fi
else
    echo -e "${RED}✗ .dmg 파일 생성 실패${NC}"
    exit 1
fi
