# 🍎 macOS용 Woori 파일 공유 프로그램 V3

## 📋 목차
- [시스템 요구사항](#-시스템-요구사항)
- [빠른 시작](#-빠른-시작)
- [상세 설치 가이드](#-상세-설치-가이드)
- [사용 방법](#-사용-방법)
- [문제 해결](#-문제-해결)
- [.app 파일 빌드](#-app-파일-빌드)

---

## 🖥 시스템 요구사항

- **macOS**: 10.14 (Mojave) 이상
- **Python**: 3.8 이상
- **메모리**: 최소 4GB RAM
- **디스크**: 500MB 여유 공간

---

## ⚡ 빠른 시작

### 1️⃣ 자동 설치 (권장)

터미널에서 다음 명령어를 실행하세요:

```bash
cd /path/to/V3/MacOS
chmod +x setup_mac.sh
./setup_mac.sh
```

설치 완료 후:
```bash
# 서버 실행
./run_server_mac.sh

# 클라이언트 실행 (다른 터미널에서)
./run_client_mac.sh
```

---

## 📚 상세 설치 가이드

### 1단계: Python 확인

```bash
python3 --version
```

Python이 없다면:
```bash
# Homebrew 설치 (없다면)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 설치
brew install python@3.11
```

### 2단계: 프로젝트 폴더로 이동

```bash
cd /path/to/V3/MacOS
```

### 3단계: 가상환경 생성

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4단계: 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements_macos.txt
```

### 5단계: Cloudflare 터널 설치 (서버용, 선택사항)

```bash
brew install cloudflare/cloudflare/cloudflared
```

### 6단계: 실행 권한 부여

```bash
chmod +x *.sh
```

---

## 💻 사용 방법

### 서버 실행

#### 방법 1: 스크립트 사용 (권장)
```bash
./run_server_mac.sh
```

#### 방법 2: 직접 실행
```bash
source venv/bin/activate
python3 unified_server_pyqt.py
```

**서버 실행 후:**
1. GUI가 표시됩니다
2. 사용할 폴더 경로 설정
3. 사용자 계정 생성
4. "서버 시작" 버튼 클릭
5. Cloudflare URL 또는 로컬 주소가 표시됩니다

### 클라이언트 실행

#### 방법 1: 스크립트 사용 (권장)
```bash
./run_client_mac.sh
```

#### 방법 2: 직접 실행
```bash
source venv/bin/activate
python3 gui_client_pyqt.py
```

**클라이언트 실행 후:**
1. 서버 URL 입력 (예: https://xxx.trycloudflare.com 또는 http://192.168.0.100:5000)
2. 아이디/비밀번호 입력
3. 로그인하여 파일 공유 시작

---

## 🎨 주요 기능

### V3 신규 기능
✨ **폴더 업로드 전체 진행률 표시** - 폴더 전체 용량과 퍼센트 실시간 표시
✨ **다운로드 완료 항목 수동 제거** - 완료 후 최종 용량 표시, ✓ 버튼으로 제거
✨ **파일/폴더 분리 업로드** - 파일 업로드, 폴더 업로드 버튼 분리
✨ **네이티브 탐색기 사용** - 익숙한 macOS Finder 다이얼로그

### 기존 기능
- 📤 파일 및 폴더 업로드 (구조 유지)
- 📥 파일 및 폴더 다운로드 (ZIP 또는 폴더 그대로)
- 📊 실시간 진행률 및 속도 표시
- 🔄 동시 다중 업로드/다운로드 (최대 3개)
- 🔒 사용자 인증 (아이디/비밀번호)
- 🌐 Cloudflare 터널 (외부 접속)
- 🔍 파일 검색 및 정렬
- ⚙️ 설정 저장 (다운로드 폴더, 접속 정보 등)

---

## 🔧 문제 해결

### 1. Python 관련

**문제**: `python3: command not found`
```bash
brew install python@3.11
```

**문제**: Python 버전이 낮음
```bash
brew upgrade python
```

### 2. PyQt5 설치 오류

```bash
# Qt 의존성 먼저 설치
brew install qt@5

# PyQt5 재설치
pip install PyQt5 --no-cache-dir --force-reinstall
```

### 3. Cloudflare 터널 오류

```bash
# cloudflared 수동 설치
brew install cloudflare/cloudflare/cloudflared

# 버전 확인
cloudflared --version
```

### 4. 가상환경 활성화 문제

```bash
# venv 삭제 후 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_macos.txt
```

### 5. 권한 문제

```bash
# 스크립트 실행 권한
chmod +x *.sh

# Python 파일 실행 권한
chmod +x *.py
```

### 6. 방화벽 문제

**시스템 환경설정 → 보안 및 개인 정보 보호 → 방화벽 → 방화벽 옵션**
- Python 허용
- 필요시 방화벽 일시 비활성화

### 7. GUI가 표시되지 않음

```bash
# XQuartz 설치 (필요한 경우)
brew install --cask xquartz

# 재부팅 후 재시도
```

---

## 📦 .app 파일 빌드

### 방법 1: 통합 빌드 (권장) ⭐

**Windows의 build_pyqt_all.bat처럼 한 번에 빌드:**

```bash
./build_all_mac.sh
```

빌드 완료 후:
- `dist/Woori_Server.app` - 서버 애플리케이션
- `dist/Woori_Client.app` - 클라이언트 애플리케이션
- `dist/Woori_파일공유_V3.dmg` - 배포용 설치 파일 ⭐

### 방법 2: .app 파일만 빌드

```bash
./build_mac_apps.sh
```

빌드 완료 후:
- `dist/Woori_Server.app` - 서버 애플리케이션
- `dist/Woori_Client.app` - 클라이언트 애플리케이션

### .app 파일 실행

1. **Finder**에서 `dist` 폴더 열기
2. `.app` 파일 더블클릭
3. **보안 경고 시**:
   - `시스템 환경설정 → 보안 및 개인 정보 보호`
   - "확인 없이 열기" 클릭

### .app 파일 배포

- 같은 Mac에서는 그대로 복사해도 작동
- 다른 Mac에 배포 시 공증(notarization) 필요할 수 있음
- 내부 네트워크 사용은 공증 불필요

---

## 🌐 크로스 플랫폼 사용

### Windows 서버 + Mac 클라이언트
1. Windows에서 서버 실행 → Cloudflare URL 생성
2. Mac에서 클라이언트 실행 → URL 입력

### Mac 서버 + Windows 클라이언트
1. Mac에서 서버 실행 → Cloudflare URL 생성
2. Windows에서 클라이언트 실행 → URL 입력

### 같은 네트워크 (LAN)
1. 서버 실행 → 로컬 IP 확인 (예: `192.168.0.100:5000`)
2. 클라이언트에서 `http://192.168.0.100:5000` 접속
3. Cloudflare 없이 빠른 전송 가능

---

## 📝 추가 정보

### 파일 경로
- **서버 설정**: `unified_server_config_pyqt.json`
- **클라이언트 설정**: `client_settings_pyqt.json`
- **로그**: 콘솔 출력 (선택적으로 파일 저장 가능)

### 포트 설정
- 기본 포트: `5000`
- 변경 방법: `unified_server_config_pyqt.json` 편집

### 보안
- 사용자 비밀번호는 해시화되어 저장됩니다
- HTTPS는 Cloudflare 터널 사용 시 자동 제공
- 로컬 네트워크는 HTTP 사용 (보안이 필요하면 VPN 권장)

### 성능 팁
- 로컬 네트워크: Cloudflare 없이 IP 직접 접속이 더 빠름
- 동시 업로드: 최대 3개 (설정 변경 가능)
- 대용량 파일: ZIP보다 폴더 그대로가 더 빠를 수 있음

---

## 🆘 지원

문제가 해결되지 않으면:
1. `사용방법_Mac.txt` 참고
2. `MAC_설치_체크리스트.txt` 확인
3. 터미널 오류 메시지 확인
4. Python 버전 및 의존성 재설치

---

## 📄 라이선스

내부 사용 목적의 프로그램입니다.

---

**제작**: Woori Team  
**버전**: V3 (2025)  
**플랫폼**: Windows, macOS 크로스 플랫폼 지원
