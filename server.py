"""
원격 파일 공유 서버 (A 컴퓨터)
공유할 폴더를 지정하면 네트워크를 통해 파일을 공유합니다.
"""
import os
import json
from pathlib import Path
from flask import Flask, render_template, send_file, request, jsonify, abort, session, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mimetypes
import secrets
import random
import string
import requests
import sys
from urllib.parse import quote
from datetime import datetime, timedelta
from collections import defaultdict

def _resource_path(rel_path: str) -> str:
    """PyInstaller 환경에서 리소스 경로를 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 경우
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # 일반 Python 실행
        base = os.path.abspath('.')
    return os.path.join(base, rel_path)

# Flask 앱 초기화
try:
    template_path = _resource_path('templates')
    if not os.path.exists(template_path):
        # 템플릿 폴더가 없으면 실행 파일과 같은 위치 시도
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app = Flask(__name__, template_folder=template_path)
except Exception as e:
    print(f"Flask 초기화 오류: {e}")
    app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # 세션 암호화 키

# 공유할 폴더 설정 (서버 실행 시 지정)
SHARED_FOLDERS = []

# 사용자 계정 (아이디: 비밀번호 해시)
USERS = {}

# 접속 코드 (서버 시작 시 자동 생성)
ACCESS_CODE = ''
SERVER_INFO = {}

# 보안: 로그인 실패 추적
login_attempts = defaultdict(list)  # IP별 로그인 시도 시간 기록
blocked_ips = {}  # IP별 차단 시간
MAX_LOGIN_ATTEMPTS = 5  # 최대 시도 횟수
ATTEMPT_WINDOW = 300  # 5분 (초)
BLOCK_DURATION = 900  # 15분 (초)

# 접속 로그
access_log = []

def get_file_info(file_path):
    """파일/폴더 정보를 가져옵니다"""
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat.st_size if os.path.isfile(file_path) else 0,
        'is_dir': os.path.isdir(file_path),
        'modified': stat.st_mtime
    }

def list_files(folder_path):
    """폴더 내 파일 목록을 가져옵니다"""
    items = []
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            try:
                items.append(get_file_info(item_path))
            except Exception as e:
                print(f"Error accessing {item_path}: {e}")
                continue
    except Exception as e:
        print(f"Error listing directory {folder_path}: {e}")
    
    return sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower()))

def login_required(f):
    """로그인 필수 데코레이터"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def add_user(username, password):
    """사용자 추가"""
    USERS[username] = generate_password_hash(password)
    print(f"✓ 사용자 추가됨: {username}")

def verify_user(username, password):
    """사용자 인증"""
    if username in USERS:
        return check_password_hash(USERS[username], password)
    return False

def get_client_ip():
    """클라이언트 IP 가져오기 (프록시 고려)"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def is_ip_blocked(ip):
    """IP 차단 여부 확인"""
    if ip in blocked_ips:
        block_time = blocked_ips[ip]
        if datetime.now() < block_time:
            remaining = int((block_time - datetime.now()).total_seconds() / 60)
            return True, remaining
        else:
            # 차단 시간 만료
            del blocked_ips[ip]
            if ip in login_attempts:
                del login_attempts[ip]
    return False, 0

def record_login_attempt(ip, success=False):
    """로그인 시도 기록"""
    now = datetime.now()
    
    if success:
        # 성공 시 기록 초기화
        if ip in login_attempts:
            del login_attempts[ip]
        if ip in blocked_ips:
            del blocked_ips[ip]
        return
    
    # 실패 시 기록 추가
    login_attempts[ip].append(now)
    
    # 5분 이전 기록 제거
    login_attempts[ip] = [t for t in login_attempts[ip] 
                          if (now - t).total_seconds() < ATTEMPT_WINDOW]
    
    # 시도 횟수 초과 시 차단
    if len(login_attempts[ip]) >= MAX_LOGIN_ATTEMPTS:
        blocked_ips[ip] = now + timedelta(seconds=BLOCK_DURATION)
        print(f"[보안] IP 차단: {ip} (15분간)")

def log_access(username, action, details=""):
    """접속 로그 기록"""
    ip = get_client_ip()
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'ip': ip,
        'username': username,
        'action': action,
        'details': details
    }
    access_log.append(log_entry)
    
    # 최근 1000개만 유지
    if len(access_log) > 1000:
        access_log.pop(0)
    
    # 콘솔 출력
    print(f"[로그] {log_entry['timestamp']} | {ip} | {username} | {action} | {details}")

def load_server_config(config_path='server_config.json'):
    """server_config.json에서 사용자/공유폴더를 로드하여 적용
    형식 예시:
    {
      "users": {"admin":"admin"},
      "shared_folders": ["D:/Share"]
    }
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            users = cfg.get('users', {})
            folders = cfg.get('shared_folders', [])
            # 사용자 적용
            if isinstance(users, dict):
                for u, p in users.items():
                    if u and p is not None:
                        add_user(str(u), str(p))
            # 폴더 적용
            if isinstance(folders, list):
                for folder in folders:
                    if folder:
                        add_shared_folder(folder)
            return True
    except Exception as e:
        print(f"설정 파일 로드 오류: {e}")
    return False

 

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if request.method == 'POST':
        # IP 차단 확인
        client_ip = get_client_ip()
        blocked, remaining = is_ip_blocked(client_ip)
        if blocked:
            error_msg = f'보안: 너무 많은 로그인 실패로 차단되었습니다.\n{remaining}분 후 다시 시도하세요.'
            log_access('차단된 IP', '로그인 차단', client_ip)
            return render_template('login.html', error=error_msg)
        
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"\n[DEBUG] 로그인 시도 - 아이디: '{username}', 비밀번호 길이: {len(password)}, IP: {client_ip}")
        print(f"[DEBUG] 등록된 사용자: {list(USERS.keys())}")
        print(f"[DEBUG] 사용자 존재 여부: {username in USERS}")
        
        if verify_user(username, password):
            print(f"[DEBUG] 로그인 성공: {username}")
            record_login_attempt(client_ip, success=True)
            log_access(username, '로그인 성공', '')
            session['username'] = username
            return redirect(url_for('index'))
        else:
            print(f"[DEBUG] 로그인 실패: {username}")
            record_login_attempt(client_ip, success=False)
            log_access(username or '알 수 없음', '로그인 실패', '')
            
            # 남은 시도 횟수 계산
            attempts = len(login_attempts.get(client_ip, []))
            remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts
            if remaining_attempts > 0:
                error_msg = f'아이디 또는 비밀번호가 올바르지 않습니다.\n(남은 시도: {remaining_attempts}회)'
            else:
                error_msg = '로그인 실패 횟수 초과. 15분 후 다시 시도하세요.'
            
            return render_template('login.html', error=error_msg)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """로그아웃"""
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """메인 페이지 - 공유 폴더 목록 표시"""
    folders = []
    for folder in SHARED_FOLDERS:
        if os.path.exists(folder):
            folders.append({
                'name': os.path.basename(folder) or folder,
                'path': folder
            })
    return render_template('index.html', folders=folders, username=session.get('username'))

@app.route('/browse')
@login_required
def browse():
    """폴더 내용 탐색"""
    folder_path = os.path.abspath(request.args.get('path', ''))
    # 보안: 공유 폴더 내에서만 접근 가능
    if not is_allowed_path(folder_path):
        abort(403)
    if not os.path.isdir(folder_path):
        abort(404)
    
    files = list_files(folder_path)
    parent = os.path.dirname(folder_path) if folder_path not in SHARED_FOLDERS else None
    
    return render_template('browse.html', 
                         current_path=folder_path, 
                         files=files, 
                         parent=parent,
                         username=session.get('username'))

@app.route('/api/check_code')
def check_code():
    """접속 코드 확인 API"""
    code = request.args.get('code', '').upper()
    if code == ACCESS_CODE:
        return jsonify({
            'valid': True,
            'users': list(USERS.keys())
        })
    return jsonify({'valid': False}), 403

@app.route('/api/ping')
def api_ping():
    """서버 존재 확인(로그인 불필요) - LAN 자동검색 용"""
    try:
        info = {
            'ok': True,
            'code': ACCESS_CODE,
            'port': 5000,
            'users': list(USERS.keys()),
            'shared_count': len([f for f in SHARED_FOLDERS if os.path.exists(f)])
        }
        # server_info.json 존재 시 IP 정보 포함
        if SERVER_INFO:
            info.update({
                'public_ip': SERVER_INFO.get('public_ip'),
                'local_ip': SERVER_INFO.get('local_ip')
            })
        return jsonify(info)
    except Exception:
        return jsonify({'ok': True, 'port': 5000})

@app.route('/api/shared_folders')
@login_required
def shared_folders():
    """공유 폴더 목록 API"""
    folders = []
    for folder in SHARED_FOLDERS:
        if os.path.exists(folder):
            folders.append(folder)
    return jsonify({'folders': folders})

@app.route('/api/files')
@login_required
def api_files():
    """파일 목록 API"""
    folder_path = os.path.abspath(request.args.get('path', ''))
    if not is_allowed_path(folder_path):
        return jsonify({'error': 'Access denied'}), 403
    if not os.path.isdir(folder_path):
        return jsonify({'error': 'Folder not found'}), 404
    
    files = list_files(folder_path)
    return jsonify({'files': files, 'current_path': folder_path})

@app.route('/download')
@login_required
def download():
    """파일 다운로드"""
    file_path = os.path.abspath(request.args.get('path', ''))
    # 보안: 공유 폴더 내에서만 접근 가능
    if not is_allowed_path(file_path):
        abort(403)
    if not os.path.isfile(file_path):
        abort(404)
    
    # 로그 기록
    log_access(session.get('username', '알 수 없음'), '파일 다운로드', os.path.basename(file_path))
    
    response = send_file(file_path, as_attachment=True, 
                        download_name=os.path.basename(file_path),
                        conditional=True)
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'no-transform'
    return response

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """파일 업로드"""
    print(f"\n[DEBUG 업로드] 요청 수신")
    print(f"[DEBUG 업로드] 세션 사용자: {session.get('username', '없음')}")
    print(f"[DEBUG 업로드] Request files: {list(request.files.keys())}")
    print(f"[DEBUG 업로드] Request form: {dict(request.form)}")
    
    try:
        if 'file' not in request.files:
            print(f"[DEBUG 업로드] 오류: 파일 없음")
            return jsonify({'error': '파일이 없습니다'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print(f"[DEBUG 업로드] 오류: 파일명 없음")
            return jsonify({'error': '파일이 선택되지 않았습니다'}), 400
        
        # 저장할 경로 (상대 경로)
        relative_path = request.form.get('relative_path', '')
        target_folder = request.form.get('target_folder', '')
        
        print(f"[DEBUG 업로드] 파일명: {file.filename}")
        print(f"[DEBUG 업로드] relative_path: {relative_path}")
        print(f"[DEBUG 업로드] target_folder: {target_folder}")
        
        if not target_folder:
            return jsonify({'error': '대상 폴더가 지정되지 않았습니다'}), 400
        
        # 보안: 공유 폴더 내에서만 업로드 가능
        target_abs = os.path.abspath(target_folder)
        if not is_allowed_path(target_abs):
            return jsonify({'error': '업로드 권한이 없습니다'}), 403
        
        # 파일 저장 경로 생성
        if relative_path:
            # 폴더 구조 유지
            full_path = os.path.join(target_abs, relative_path)
        else:
            # 단일 파일
            full_path = os.path.join(target_abs, secure_filename(file.filename))
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # 파일 저장
        file.save(full_path)
        
        # 로그 기록
        log_access(session.get('username', '알 수 없음'), '파일 업로드', 
                  f"{os.path.basename(full_path)} -> {target_folder}")
        
        return jsonify({'success': True, 'path': full_path})
    
    except Exception as e:
        print(f"[업로드 오류] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_folder')
@login_required
def download_folder():
    """폴더를 ZIP으로 다운로드 (스트리밍 최적화)"""
    import zipfile
    import tempfile
    
    folder_path = os.path.abspath(request.args.get('path', ''))
    comp_q = (request.args.get('comp', '') or request.args.get('compression', '')).strip().lower()
    # 기본: 비압축(가장 빠름). comp=deflate일 때만 압축
    if comp_q in ('deflate', 'zip_deflated', '1', 'true', 'yes'):
        zip_mode = zipfile.ZIP_DEFLATED
        z_kwargs = {'compresslevel': 1}
    else:
        zip_mode = zipfile.ZIP_STORED
        z_kwargs = {}
    if not is_allowed_path(folder_path):
        abort(403)
    if not os.path.isdir(folder_path):
        abort(404)
    
    folder_name = os.path.basename(folder_path)
    
    # 로그 기록
    log_access(session.get('username', '알 수 없음'), '폴더 다운로드 시작', folder_name)
    print(f"\n[폴더 다운로드] 시작: {folder_name}")
    print(f"[폴더 다운로드] 경로: {folder_path}")
    
    # 임시 파일 경로 준비 및 ZIP 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        tmp_path = tmp.name
    
    try:
        file_count = 0
        print(f"[폴더 다운로드] ZIP 압축 시작...")
        with zipfile.ZipFile(tmp_path, 'w', zip_mode, allowZip64=True, **z_kwargs) as zf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    try:
                        zf.write(file_path, arcname)
                        file_count += 1
                        if file_count % 100 == 0:
                            print(f"[폴더 다운로드] 압축 중... {file_count}개 파일 처리됨")
                    except Exception as e:
                        print(f"[오류] 파일 추가 실패 {file_path}: {e}")
        
        total_size = os.path.getsize(tmp_path)
        print(f"[폴더 다운로드] ZIP 압축 완료: {file_count}개 파일, {total_size:,} bytes")
        log_access(session.get('username', '알 수 없음'), '폴더 다운로드 준비완료', f"{folder_name} ({file_count}개 파일)")
        
    except Exception as e:
        print(f"[오류] ZIP 압축 실패: {e}")
        log_access(session.get('username', '알 수 없음'), '폴더 다운로드 실패', f"{folder_name} - {str(e)}")
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass
        raise

    def generate_zip():
        try:
            with open(tmp_path, 'rb') as f:
                while True:
                    chunk = f.read(4*1024*1024)
                    if not chunk:
                        break
                    yield chunk
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass

    safe_name = secure_filename(folder_name) or "folder"
    utf8_name = quote(f"{folder_name}.zip")
    content_disposition = f"attachment; filename=\"{safe_name}.zip\"; filename*=UTF-8''{utf8_name}"
    response = app.response_class(
        generate_zip(),
        mimetype='application/zip',
        headers={
            'Content-Disposition': content_disposition,
            'Content-Type': 'application/zip',
            'Content-Length': str(total_size)
        }
    )
    return response

def add_shared_folder(folder_path):
    """공유 폴더 추가"""
    folder_path = os.path.abspath(folder_path)
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        if folder_path not in SHARED_FOLDERS:
            SHARED_FOLDERS.append(folder_path)
            print(f"✓ 공유 폴더 추가됨: {folder_path}")
            return True
    else:
        print(f"✗ 폴더가 존재하지 않음: {folder_path}")
        return False

def is_allowed_path(target_path: str) -> bool:
    """요청 경로가 공유 폴더 하위인지 안전하게 검사"""
    try:
        target_abs = os.path.abspath(target_path)
        for shared in SHARED_FOLDERS:
            base = os.path.abspath(shared)
            try:
                common = os.path.commonpath([target_abs, base])
            except Exception:
                continue
            if common == base:
                return True
        return False
    except Exception:
        return False

def generate_access_code():
    """접속 코드 생성 (6자리 영숫자)"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_public_ip():
    """공인 IP 주소 확인"""
    try:
        # 여러 서비스 시도
        services = [
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'https://icanhazip.com',
            'https://ident.me'
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    return response.text.strip()
            except:
                continue
    except:
        pass
    return None

def get_local_ip():
    """로컬 IP 주소 확인"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return None

def save_server_info():
    """서버 정보 저장"""
    global ACCESS_CODE, SERVER_INFO
    
    # 접속 코드 생성
    ACCESS_CODE = generate_access_code()
    
    # IP 주소 확인
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    
    # 서버 정보 저장
    SERVER_INFO = {
        'access_code': ACCESS_CODE,
        'users': {username: USERS[username] for username in USERS.keys()},
        'port': 5000,
        'public_ip': public_ip,
        'local_ip': local_ip
    }
    
    # 파일로 저장
    try:
        with open('server_info.json', 'w', encoding='utf-8') as f:
            json.dump(SERVER_INFO, f, indent=4, ensure_ascii=False)
    except:
        pass
    
    return ACCESS_CODE, public_ip, local_ip

# WSGI(예: waitress-serve server:app)로 구동될 때도
# 설정과 접속코드가 초기화되도록 시도
try:
    # 기본값 없으면 최소 한 개는 채움
    if not USERS:
        add_user('admin', 'admin')
    if not SHARED_FOLDERS:
        add_shared_folder(os.getcwd())
    # server_config.json 존재 시 우선 적용
    if os.path.exists('server_config.json'):
        load_server_config('server_config.json')
    if not ACCESS_CODE:
        save_server_info()
except Exception:
    pass

def main():
    """서버 시작"""
    import socket
    def _port_in_use(host: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((host, port)) == 0
        except Exception:
            return False

    # 이미 실행 중이면 중복 실행 방지
    if _port_in_use('127.0.0.1', 5000) or _port_in_use('0.0.0.0', 5000):
        print('[INFO] Server already running on port 5000. Exit.')
        return
    print("=" * 60)
    print("원격 파일 공유 서버")
    print("=" * 60)
    auto_mode = ('--auto' in sys.argv) or os.path.exists('server_config.json')
    if auto_mode:
        print("\n[자동모드] server_config.json을 이용해 서버를 설정합니다.")
        loaded = load_server_config('server_config.json')
        if not loaded:
            # 설정 파일이 없거나 오류 시 기본값 적용
            if not USERS:
                add_user('admin', 'admin')
            if not SHARED_FOLDERS:
                add_shared_folder(os.getcwd())
        print("[자동모드] 설정 완료")
    else:
        # 사용자 계정 설정 (대화형)
        print("\n[1단계] 로그인 계정 설정")
        print("-" * 60)
        while True:
            username = input("아이디 (완료 시 빈 줄 입력): ").strip()
            if not username:
                break
            password = input(f"{username}의 비밀번호: ").strip()
            if password:
                add_user(username, password)
        
        if not USERS:
            print("\n계정이 없습니다. 기본 계정을 생성합니다.")
            add_user('admin', 'admin')
            print("⚠️  기본 계정 - 아이디: admin, 비밀번호: admin")
        
        # 공유 폴더 입력
        print("\n[2단계] 공유 폴더 설정")
        print("-" * 60)
        print("공유할 폴더 경로를 입력하세요 (여러 개 가능, 완료 시 빈 줄 입력):")
        while True:
            folder = input("폴더 경로: ").strip()
            if not folder:
                break
            add_shared_folder(folder)
        
        if not SHARED_FOLDERS:
            print("\n공유 폴더가 없습니다. 기본 폴더를 공유합니다.")
            add_shared_folder(os.getcwd())
    
    # 접속 코드 생성 및 저장
    print("\n공인 IP 주소를 확인하는 중...")
    access_code, public_ip, local_ip = save_server_info()
    
    print("\n" + "=" * 60)
    print("서버 설정 완료")
    print("=" * 60)
    print("\n등록된 사용자:")
    for username in USERS.keys():
        print(f"  - {username}")
    
    print("\n공유 중인 폴더:")
    for folder in SHARED_FOLDERS:
        print(f"  - {folder}")
    
    print("\n" + "=" * 60)
    print("⭐ 사용 안내")
    print("=" * 60)
    if local_ip:
        print(f"  같은 네트워크 접속: http://{local_ip}:5000")
    print("  원거리 접속: key_oneclick.exe 로 발급된 키(URL)를 클라이언트 '접속키'에 붙여넣기")
    print("  (공인 IP/포트포워딩 불필요)")
    print("" )
    print("=" * 60)
    
    print("\n서버를 시작합니다...")
    print("외부 접속을 위해 0.0.0.0:5000 으로 실행합니다.")
    print("\n종료하려면 Ctrl+C 를 누르세요.")
    print("=" * 60)
    
    # 서버 실행
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller 실행 파일 환경: waitress로 서비스
            try:
                from waitress import serve
                print("[INFO] Starting server with waitress...")
                serve(app, listen='0.0.0.0:5000', threads=64)
            except ImportError as ie:
                print(f'[WARNING] waitress not available: {ie}')
                print('[INFO] Falling back to Flask development server...')
                app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
        else:
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print('\n[INFO] Server stopped by user.')
    except Exception as e:
        print(f'[ERROR] Failed to start server: {e}')
        import traceback
        traceback.print_exc()
        input('Press Enter to exit...')

if __name__ == '__main__':
    main()
