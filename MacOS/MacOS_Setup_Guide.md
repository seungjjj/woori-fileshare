# macOS용 파일 공유 프로그램 설치 가이드

## 📋 준비 사항

1. **Python 3.8 이상 설치 확인**
   ```bash
   python3 --version
   ```

2. **Homebrew 설치** (없다면)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

---

## 🚀 설치 및 실행 방법

### 1️⃣ 프로젝트 폴더로 이동
```bash
cd /path/to/파일공유프로그램/V3
```

### 2️⃣ 가상환경 생성
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements_macos.txt
```

### 4️⃣ 실행 권한 부여
```bash
chmod +x run_server_mac.sh
chmod +x run_client_mac.sh
chmod +x build_mac_apps.sh
```

---

## 💻 실행 방법

### 서버 실행
```bash
./run_server_mac.sh
```
또는
```bash
source venv/bin/activate
python3 unified_server_pyqt.py
```

### 클라이언트 실행
```bash
./run_client_mac.sh
```
또는
```bash
source venv/bin/activate
python3 gui_client_pyqt.py
```

---

## 📦 .app 파일 생성 (배포용)

### .app 파일 빌드
```bash
./build_mac_apps.sh
```

빌드 완료 후:
- `dist/Woori_Server.app` - 서버 애플리케이션
- `dist/Woori_Client.app` - 클라이언트 애플리케이션

### .app 파일 실행
1. Finder에서 `dist` 폴더 열기
2. `.app` 파일 더블클릭
3. "보안" 경고 시: **시스템 환경설정 → 보안 및 개인 정보 보호 → "확인 없이 열기"**

---

## 🔧 문제 해결

### Python 버전 문제
```bash
# Python 3 확인
which python3
python3 --version

# 필요시 Homebrew로 설치
brew install python@3.11
```

### PyQt5 설치 오류
```bash
# Qt 의존성 설치
brew install qt@5
pip install PyQt5 --no-cache-dir
```

### Cloudflare 터널 오류
```bash
# cloudflared 수동 설치
brew install cloudflare/cloudflare/cloudflared
```

### 권한 문제
```bash
# 실행 권한 부여
chmod +x *.sh
```

---

## 📝 참고사항

1. **서버와 클라이언트는 독립적으로 실행**
   - 서버: Windows나 Mac 어디서든 실행 가능
   - 클라이언트: Mac에서 Windows 서버에 접속 가능

2. **방화벽 설정**
   - macOS 방화벽에서 Python 허용 필요
   - 시스템 환경설정 → 보안 및 개인 정보 보호 → 방화벽

3. **.app 파일 배포**
   - 다른 Mac에 배포 시 공증(notarization) 필요할 수 있음
   - 내부 사용은 그냥 복사해도 작동

---

## 🌐 크로스 플랫폼 사용 예시

### 시나리오 1: Windows 서버 + Mac 클라이언트
1. Windows에서 서버 실행 → Cloudflare URL 생성
2. Mac에서 클라이언트 실행 → URL 입력하여 접속

### 시나리오 2: Mac 서버 + Windows 클라이언트
1. Mac에서 서버 실행 → Cloudflare URL 생성
2. Windows에서 클라이언트 실행 → URL 입력하여 접속

### 시나리오 3: 같은 네트워크 (LAN)
1. 서버 실행 → 로컬 IP 확인 (예: 192.168.0.100:5000)
2. 클라이언트에서 `http://192.168.0.100:5000` 접속
