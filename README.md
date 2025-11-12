# 🚀 Woori 파일 공유 프로그램 V3

크로스 플랫폼 파일 공유 프로그램 (Windows + macOS)

## ✨ 주요 기능

- 📤 **파일/폴더 업로드** - 다중 선택 및 폴더 구조 유지
- 📥 **파일/폴더 다운로드** - ZIP 또는 폴더 그대로
- 📊 **실시간 진행률** - 전체 폴더 진행률 및 속도 표시
- 🔄 **동시 다중 전송** - 최대 3개 동시 업로드/다운로드
- 🔒 **사용자 인증** - 아이디/비밀번호 보안
- 🌐 **Cloudflare 터널** - 외부 접속 지원
- 💻 **크로스 플랫폼** - Windows ↔ macOS 완벽 호환

## 🎨 V3 신규 기능

✨ **폴더 업로드 전체 진행률** - 폴더 전체 용량과 퍼센트 실시간 표시  
✨ **완료 항목 수동 제거** - 최종 용량 표시, ✓ 버튼으로 제거  
✨ **파일/폴더 분리 업로드** - 파일/폴더 업로드 버튼 분리  
✨ **네이티브 탐색기** - 익숙한 OS 파일 선택 창

## 📦 다운로드

### Windows
빌드된 .exe 파일은 Releases 페이지에서 다운로드하세요.

### macOS
자동 빌드된 .dmg 파일은 Actions 탭의 Artifacts에서 다운로드하세요.

## 🚀 빠른 시작

### Windows
```batch
# 서버 실행
test_server_pyqt.bat

# 클라이언트 실행
test_client_pyqt.bat
```

### macOS
```bash
cd MacOS
./setup_mac.sh        # 최초 1회
./run_server_mac.sh   # 서버
./run_client_mac.sh   # 클라이언트
```

## 🔧 개발

### 요구사항
- Python 3.8+
- PyQt5
- Flask
- requests

### Windows 빌드
```batch
build_pyqt_all.bat
```

### macOS 빌드
```bash
cd MacOS
./build_all_mac.sh
```

## 📚 문서

- [Windows 사용 방법](사용방법_Windows.txt)
- [macOS 빠른 시작](MacOS/빠른시작_MacOS.txt)
- [macOS 상세 가이드](MacOS/README_MacOS.md)
- [GitHub Actions 가이드](MacOS/GitHub_Actions_가이드.txt)

## 🌐 크로스 플랫폼 사용

- ✅ Windows 서버 + Mac 클라이언트
- ✅ Mac 서버 + Windows 클라이언트
- ✅ 같은 플랫폼 간 연결
- ✅ 로컬 네트워크 또는 Cloudflare 터널

## 📄 라이선스

내부 사용 목적의 프로그램입니다.

---

**제작**: Woori Team  
**버전**: V3 (2025)  
**플랫폼**: Windows, macOS
