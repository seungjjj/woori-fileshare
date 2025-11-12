"""
파일 공유 클라이언트 - PyQt5 모던 버전
블랙/화이트 프리미어 다크 스타일
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime
import time
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QProgressBar, QMessageBox, QFileDialog, QScrollArea, QFrame,
    QCheckBox, QComboBox, QTextEdit, QGraphicsOpacityEffect, QMenu,
    QListWidget, QInputDialog, QListView, QTreeView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette

import requests
from requests.adapters import HTTPAdapter

# 다크 테마 QSS 스타일시트
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: "맑은 고딕";
    font-size: 10pt;
}

QLabel {
    color: #ffffff;
    background-color: transparent;
}

QLineEdit {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 8px;
    font-size: 10pt;
}

QLineEdit:focus {
    border: 1px solid #2563eb;
}

QPushButton {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 10pt;
}

QPushButton:hover {
    background-color: #e0e0e0;
}

QPushButton:pressed {
    background-color: #d0d0d0;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QTreeWidget {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #333333;
    alternate-background-color: #0a0a0a;
}

QTreeWidget::item {
    padding: 5px;
    border-bottom: 1px solid #1a1a1a;
}

QTreeWidget::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

QTreeWidget::item:hover {
    background-color: #1a1a1a;
}

QHeaderView::section {
    background-color: #1a1a1a;
    color: #ffffff;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #333333;
    font-weight: bold;
}

QProgressBar {
    background-color: #1a1a1a;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #2563eb;
    border-radius: 4px;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #444444;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QCheckBox {
    color: #ffffff;
    spacing: 5px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #333333;
    border-radius: 3px;
    background-color: #1a1a1a;
}

QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #2563eb;
}

QComboBox {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 5px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    color: #ffffff;
    selection-background-color: #2563eb;
}

/* 다운로드 항목 프레임 */
QFrame#downloadItem {
    background-color: #1a1a1a;
    border: 1px solid #333333;
    border-radius: 4px;
    margin: 2px 0px;
}

/* 취소 버튼 */
QPushButton#cancelBtn {
    background-color: #dc2626;
    color: #ffffff;
    min-width: 30px;
    max-width: 30px;
    padding: 5px;
}

QPushButton#cancelBtn:hover {
    background-color: #ef4444;
}

/* 일시정지 버튼 */
QPushButton#pauseBtn {
    background-color: #ffffff;
    color: #000000;
    min-width: 30px;
    max-width: 30px;
    padding: 5px;
}
"""


class DownloadTask:
    """다운로드 작업"""
    def __init__(self, file_path, file_name, save_path, total_size=0):
        self.file_path = file_path
        self.file_name = file_name
        self.save_path = save_path
        self.total_size = total_size
        self.downloaded = 0
        self.status = 'waiting'
        self.cancel_flag = False
        self.pause_flag = False
        self.error_msg = None
        self.speed = 0
        self.start_time = None


class UploadTask:
    """업로드 작업"""
    def __init__(self, local_path, target_folder, relative_path=''):
        self.local_path = local_path  # 로컬 파일 경로
        self.target_folder = target_folder  # 서버 대상 폴더
        self.relative_path = relative_path  # 폴더 구조 유지용 상대 경로
        self.file_name = os.path.basename(local_path) if not relative_path else relative_path
        self.total_size = os.path.getsize(local_path) if os.path.isfile(local_path) else 0
        self.uploaded = 0
        self.status = 'waiting'
        self.cancel_flag = False
        self.pause_flag = False
        self.error_msg = None
        self.speed = 0
        self.start_time = None
        self.batch_id = None
        self.last_reported = 0


class UploadThread(QThread):
    """업로드 스레드"""
    progress = pyqtSignal(int, str, int, int)  # 진행률, 속도, 업로드된 크기, 전체 크기
    finished = pyqtSignal(bool, str)  # 성공여부, 메시지
    
    def __init__(self, task, server_url, session):
        super().__init__()
        self.task = task
        self.server_url = server_url
        self.session = session
    
    def run(self):
        try:
            self.task.status = 'uploading'
            self.task.start_time = time.time()
            
            url = f"{self.server_url}/upload"
            debug_info = f"[DEBUG 업로드 요청]"
            debug_info += f"\n  - URL: {url}"
            debug_info += f"\n  - 파일: {os.path.basename(self.task.local_path)}"
            debug_info += f"\n  - 전체경로: {self.task.local_path}"
            debug_info += f"\n  - target_folder: {self.task.target_folder}"
            debug_info += f"\n  - relative_path: {self.task.relative_path}"
            debug_info += f"\n  - 파일크기: {self.task.total_size:,} bytes"
            print(debug_info)
            # UI 로그에도 출력 (부모 위젯에서 add_log 호출)
            if hasattr(self.parent(), 'add_log'):
                self.parent().add_log(debug_info)
            
            # 파일을 청크로 읽어서 업로드 진행률 추적
            try:
                from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
                use_toolbelt = True
            except ImportError:
                use_toolbelt = False
            
            if use_toolbelt:
                # requests_toolbelt 사용 (진행률 추적 가능)
                with open(self.task.local_path, 'rb') as f:
                    encoder = MultipartEncoder(
                        fields={
                            'file': (os.path.basename(self.task.local_path), f, 'application/octet-stream'),
                            'target_folder': self.task.target_folder,
                            'relative_path': self.task.relative_path
                        }
                    )
                    
                    def callback(monitor):
                        if self.task.cancel_flag:
                            return
                        
                        self.task.uploaded = monitor.bytes_read
                        elapsed = time.time() - self.task.start_time
                        if elapsed > 0:
                            self.task.speed = self.task.uploaded / elapsed
                        
                        if self.task.total_size > 0:
                            percent = int((self.task.uploaded / self.task.total_size) * 100)
                            speed_mb = self.task.speed / (1024 * 1024)
                            self.progress.emit(percent, f"{speed_mb:.1f} MB/s",
                                             self.task.uploaded, self.task.total_size)
                    
                    monitor = MultipartEncoderMonitor(encoder, callback)
                    
                    response = self.session.post(
                        url,
                        data=monitor,
                        headers={'Content-Type': monitor.content_type},
                        timeout=300
                    )
            else:
                # 기본 requests 사용 (진행률 추적 불가)
                with open(self.task.local_path, 'rb') as f:
                    files = {'file': (os.path.basename(self.task.local_path), f)}
                    data = {
                        'target_folder': self.task.target_folder,
                        'relative_path': self.task.relative_path
                    }
                    
                    # 간단한 진행률 표시 (업로드 시작/완료만)
                    self.progress.emit(50, "업로드 중...", self.task.total_size // 2, self.task.total_size)
                    
                    response = self.session.post(url, files=files, data=data, timeout=300)
            
            response_info = f"[DEBUG 업로드 응답]"
            response_info += f"\n  - 상태코드: {response.status_code}"
            response_info += f"\n  - 응답내용: {response.text[:500]}"
            print(response_info)
            if hasattr(self.parent(), 'add_log'):
                self.parent().add_log(response_info)
            
            if response.status_code == 200:
                self.task.status = 'completed'
                self.task.uploaded = self.task.total_size
                self.progress.emit(100, "완료", self.task.total_size, self.task.total_size)
                self.finished.emit(True, "완료")
            else:
                raise Exception(f"서버 오류: {response.status_code}")
        
        except Exception as e:
            error_detail = f"[DEBUG] 업로드 예외: {str(e)}"
            print(error_detail)
            if hasattr(self.parent(), 'add_log'):
                self.parent().add_log(error_detail)
            self.task.status = 'error'
            self.task.error_msg = str(e)
            self.finished.emit(False, f"오류: {e}")


class DownloadThread(QThread):
    """다운로드 스레드"""
    progress = pyqtSignal(int, str, int, int)  # 진행률, 속도, 다운로드된 크기, 전체 크기
    finished = pyqtSignal(bool, str)  # 성공여부, 메시지
    
    def __init__(self, task, server_url, session, is_folder=False):
        super().__init__()
        self.task = task
        self.server_url = server_url
        self.session = session
        self.is_folder = is_folder
    
    def run(self):
        try:
            self.task.status = 'downloading'
            self.task.start_time = time.time()
            
            # 폴더/파일에 따라 엔드포인트 선택
            if self.is_folder:
                # 폴더는 ZIP으로만 다운로드 (서버에서 압축)
                url = f"{self.server_url}/download_folder"
                # 폴더는 압축 시간이 필요하므로 타임아웃을 길게 설정
                timeout = 300  # 5분
            else:
                url = f"{self.server_url}/download"
                timeout = 60  # 1분
            
            params = {'path': self.task.file_path}
            
            # 재시도 로직 (최대 2번)
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, params=params, stream=True, timeout=timeout)
                    response.raise_for_status()
                    break  # 성공하면 루프 탈출
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[재시도] {attempt + 1}번째 시도 실패, 재시도 중... ({e})")
                        time.sleep(2)  # 2초 대기 후 재시도
                    else:
                        raise  # 마지막 시도에서도 실패하면 예외 발생
            
            self.task.total_size = int(response.headers.get('content-length', 0))
            self.task.downloaded = 0
            
            with open(self.task.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1048576):
                    if self.task.cancel_flag:
                        # 취소 시 부분 파일 삭제
                        try:
                            f.close()
                            if os.path.exists(self.task.save_path):
                                os.remove(self.task.save_path)
                                print(f"[취소] 부분 파일 삭제: {self.task.save_path}")
                        except Exception as del_err:
                            print(f"[취소] 파일 삭제 실패: {del_err}")
                        self.finished.emit(False, "취소됨")
                        return
                    
                    while self.task.pause_flag and not self.task.cancel_flag:
                        time.sleep(0.1)
                    
                    if chunk:
                        f.write(chunk)
                        self.task.downloaded += len(chunk)
                        
                        elapsed = time.time() - self.task.start_time
                        if elapsed > 0:
                            self.task.speed = self.task.downloaded / elapsed
                        
                        if self.task.total_size > 0:
                            percent = int((self.task.downloaded / self.task.total_size) * 100)
                            speed_mb = self.task.speed / (1024 * 1024)
                            self.progress.emit(percent, f"{speed_mb:.1f} MB/s", 
                                             self.task.downloaded, self.task.total_size)
            
            self.task.status = 'completed'
            
            # 폴더 다운로드이고 압축 해제 모드인 경우
            if self.is_folder and hasattr(self.task, 'auto_extract') and self.task.auto_extract:
                try:
                    import zipfile
                    extract_dir = self.task.save_path[:-4]  # .zip 제거
                    with zipfile.ZipFile(self.task.save_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    # 압축 파일 삭제
                    os.remove(self.task.save_path)
                    self.finished.emit(True, f"완료 (압축 해제)")
                except Exception as e:
                    self.finished.emit(True, f"완료 (압축 해제 실패: {e})")
            else:
                self.finished.emit(True, "완료")
            
        except Exception as e:
            self.task.status = 'error'
            self.task.error_msg = str(e)
            # 오류 시 부분 파일 삭제
            try:
                if os.path.exists(self.task.save_path):
                    os.remove(self.task.save_path)
                    print(f"[오류] 부분 파일 삭제: {self.task.save_path}")
            except Exception as del_err:
                print(f"[오류] 파일 삭제 실패: {del_err}")
            self.finished.emit(False, f"오류: {e}")


class DownloadItemWidget(QWidget):
    """다운로드 항목 위젯"""
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(3)
        
        # 상단: 파일명과 버튼
        top_layout = QHBoxLayout()
        
        self.name_label = QLabel(self.task.file_name)
        self.name_label.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        top_layout.addWidget(self.name_label, 1)
        
        self.pause_btn = QPushButton("⏸")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setFixedSize(30, 30)
        top_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.setFixedSize(30, 30)
        top_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(top_layout)
        
        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 상태 라벨
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("color: #999999; font-size: 8pt;")
        layout.addWidget(self.status_label)
        
        # 프레임 스타일
        self.setObjectName("downloadItem")
        self.setStyleSheet("QWidget#downloadItem { background-color: #1a1a1a; border: 1px solid #333333; border-radius: 4px; }")


class FileShareClient(QMainWindow):
    """PyQt5 파일 공유 클라이언트"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("파일 공유 클라이언트 - PyQt5")
        self.resize(660, 800)
        
        # 화면 중앙 배치
        self.center_on_screen()
        
        # 다운로드 중 여부 플래그
        self.has_active_downloads = False
        
        # HTTP 세션
        self.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=32, pool_maxsize=64, max_retries=2)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.server_url = None
        self.current_path = None
        self.download_tasks = []
        self.download_widgets = {}
        # 업로드 배치(폴더 전체) 진행 관리
        self.upload_batches = {}
        self.upload_batch_widgets = {}
        
        # 설정 로드
        self.load_settings()
        
        # UI 생성
        self.show_login()
    
    def center_on_screen(self):
        """화면 중앙에 배치"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def load_settings(self):
        """설정 로드"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.config_file = os.path.join(base_dir, "client_settings_pyqt.json")
        self.settings = {}
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
        except:
            pass
        
        self.download_dir = self.settings.get('download_dir', 
                                             str(Path.home() / "Downloads" / "RemoteFiles"))
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 기본값 설정
        if 'folder_download_mode' not in self.settings:
            self.settings['folder_download_mode'] = 'zip'
        if 'duplicate_mode' not in self.settings:
            self.settings['duplicate_mode'] = 'overwrite'
    
    def save_settings(self):
        """설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 오류: {e}")
    
    def show_login(self):
        """로그인 화면"""
        # 기존 위젯 제거
        if hasattr(self, 'central_widget'):
            self.central_widget.deleteLater()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)
        
        # 제목
        title = QLabel("파일 공유 클라이언트")
        title.setFont(QFont("맑은 고딕", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # 저장된 서버 목록
        saved_servers = self.settings.get('saved_servers', {})
        if saved_servers:
            server_label = QLabel("💾 저장된 서버 (더블클릭: 접속 | 우클릭: 삭제)")
            server_label.setStyleSheet("color: #00ff00;")
            layout.addWidget(server_label)
            self.server_list = QListWidget()
            self.server_list.setMaximumHeight(100)
            for server_name in saved_servers.keys():
                self.server_list.addItem(server_name)
            self.server_list.itemDoubleClicked.connect(self.load_saved_server)
            self.server_list.setContextMenuPolicy(Qt.CustomContextMenu)
            self.server_list.customContextMenuRequested.connect(self.show_server_context_menu)
            layout.addWidget(self.server_list)
            layout.addSpacing(10)
        
        layout.addSpacing(10)
        
        # 접속키
        layout.addWidget(QLabel("접속키:"))
        self.key_entry = QLineEdit()
        self.key_entry.setPlaceholderText("https://...")
        self.key_entry.setText(self.settings.get('last_key_url', ''))
        layout.addWidget(self.key_entry)
        
        # 아이디
        layout.addWidget(QLabel("아이디:"))
        self.username_entry = QLineEdit()
        self.username_entry.setText(self.settings.get('last_username', ''))
        layout.addWidget(self.username_entry)
        
        # 비밀번호
        layout.addWidget(QLabel("비밀번호:"))
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setText(self.settings.get('last_password', ''))
        layout.addWidget(self.password_entry)
        
        layout.addSpacing(10)
        
        # 접속 버튼
        login_btn = QPushButton("접속")
        login_btn.setFont(QFont("맑은 고딕", 12, QFont.Bold))
        login_btn.setMinimumHeight(50)
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn)
        
        layout.addStretch()
        
        # Enter 키 연결
        self.password_entry.returnPressed.connect(self.login)
    
    def login(self):
        """로그인"""
        key = self.key_entry.text().strip()
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip()
        
        print(f"\n[DEBUG 클라이언트] 로그인 시도")
        print(f"  접속키: {key}")
        print(f"  아이디: '{username}' (길이: {len(username)})")
        print(f"  비밀번호 길이: {len(password)}")
        
        if not key or not username or not password:
            QMessageBox.warning(self, "경고", "모든 항목을 입력하세요.")
            return
        
        if not key.startswith("http://") and not key.startswith("https://"):
            key = "https://" + key
        
        self.server_url = key.rstrip('/')
        
        try:
            print(f"[DEBUG 클라이언트] POST 요청: {self.server_url}/login")
            response = self.session.post(f"{self.server_url}/login",
                                        data={'username': username, 'password': password},
                                        timeout=10)
            
            print(f"[DEBUG 클라이언트] 응답 상태: {response.status_code}")
            print(f"[DEBUG 클라이언트] 응답 URL: {response.url}")
            
            if response.status_code == 200 and '/login' not in response.url:
                print(f"[DEBUG 클라이언트] 로그인 성공!")
                # 설정 저장
                self.settings['last_key_url'] = self.server_url
                self.settings['last_username'] = username
                self.settings['last_password'] = password
                self.save_settings()
                
                # 서버 이름 지정 여부 확인
                self.check_and_save_server(self.server_url, username, password)
                
                self.show_file_browser()
            else:
                print(f"[DEBUG 클라이언트] 로그인 실패")
                QMessageBox.critical(self, "오류", "로그인 실패!\n아이디 또는 비밀번호를 확인하세요.")
        
        except Exception as e:
            print(f"[DEBUG 클라이언트] 예외 발생: {e}")
            QMessageBox.critical(self, "오류", f"서버 연결 실패:\n{e}")
    
    def check_and_save_server(self, server_url, username, password):
        """서버 저장 여부 확인 및 저장"""
        saved_servers = self.settings.get('saved_servers', {})
        
        # 이미 저장된 서버인지 확인
        for name, info in saved_servers.items():
            if info.get('url') == server_url and info.get('username') == username:
                # 이미 저장됨
                return
        
        # 새 서버 - 이름 입력 요청
        server_name, ok = QInputDialog.getText(
            self, 
            "서버 저장", 
            "이 서버를 저장하시겠습니까?\n저장할 이름을 입력하세요:\n(예: 사당점, 인천점 등)",
            QLineEdit.Normal,
            ""
        )
        
        if ok and server_name.strip():
            server_name = server_name.strip()
            
            # 중복 이름 확인
            if server_name in saved_servers:
                reply = QMessageBox.question(
                    self, 
                    "중복 확인",
                    f"'{server_name}' 이름이 이미 존재합니다.\n덮어쓰시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # 서버 정보 저장
            if 'saved_servers' not in self.settings:
                self.settings['saved_servers'] = {}
            
            self.settings['saved_servers'][server_name] = {
                'url': server_url,
                'username': username,
                'password': password
            }
            self.save_settings()
            QMessageBox.information(self, "저장 완료", f"'{server_name}'(으)로 저장되었습니다!")
    
    def load_saved_server(self, item):
        """저장된 서버 불러오기"""
        server_name = item.text()
        saved_servers = self.settings.get('saved_servers', {})
        
        if server_name in saved_servers:
            server_info = saved_servers[server_name]
            self.key_entry.setText(server_info.get('url', ''))
            self.username_entry.setText(server_info.get('username', ''))
            self.password_entry.setText(server_info.get('password', ''))
            
            # 자동 로그인
            self.login()
    
    def show_server_context_menu(self, position):
        """저장된 서버 우클릭 메뉴"""
        item = self.server_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        delete_action = menu.addAction("🗑️ 삭제")
        
        action = menu.exec_(self.server_list.mapToGlobal(position))
        
        if action == delete_action:
            server_name = item.text()
            reply = QMessageBox.question(
                self,
                "서버 삭제",
                f"'{server_name}'을(를) 삭제하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                saved_servers = self.settings.get('saved_servers', {})
                if server_name in saved_servers:
                    del saved_servers[server_name]
                    self.settings['saved_servers'] = saved_servers
                    self.save_settings()
                    # 화면 새로고침
                    self.show_login()
    
    def show_file_browser(self):
        """파일 브라우저 표시"""
        # 기존 위젯 제거
        if hasattr(self, 'central_widget'):
            self.central_widget.deleteLater()
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 툴바
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        back_btn = QPushButton("◀ 뒤로")
        back_btn.clicked.connect(self.go_back)
        toolbar_layout.addWidget(back_btn)
        
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        layout.addWidget(toolbar)
        
        # 경로 표시
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(5, 5, 5, 5)
        path_layout.addWidget(QLabel("위치:"))
        
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("background-color: #1a1a1a; padding: 5px; border-radius: 3px;")
        path_layout.addWidget(self.path_label, 1)
        layout.addWidget(path_widget)
        
        # 파일 목록
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["☐", "이름", "수정일"])
        self.file_tree.setColumnWidth(0, 40)
        self.file_tree.setColumnWidth(1, 360)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSelectionMode(QTreeWidget.ExtendedSelection)  # Shift/Ctrl 선택 가능
        self.file_tree.setSortingEnabled(True)  # 컬럼 클릭 정렬 활성화
        self.file_tree.sortByColumn(1, Qt.AscendingOrder)  # 기본: 이름순 정렬
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.file_tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.file_tree)
        
        # 다운로드/업로드 버튼
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        
        download_btn = QPushButton("📥 선택 다운로드")
        download_btn.clicked.connect(self.download_selected)
        btn_layout.addWidget(download_btn)
        
        upload_files_btn = QPushButton("📤 파일 업로드")
        upload_files_btn.clicked.connect(self.upload_files_only)
        btn_layout.addWidget(upload_files_btn)

        upload_folder_btn = QPushButton("📤 폴더 업로드")
        upload_folder_btn.clicked.connect(self.upload_folder_only)
        btn_layout.addWidget(upload_folder_btn)
        
        open_folder_btn = QPushButton("📂 폴더 열기")
        open_folder_btn.clicked.connect(self.open_download_folder)
        btn_layout.addWidget(open_folder_btn)
        
        set_path_btn = QPushButton("⚙ 경로 설정")
        set_path_btn.clicked.connect(self.set_download_path)
        btn_layout.addWidget(set_path_btn)
        
        select_all_btn = QPushButton("☑ 전체 선택")
        select_all_btn.clicked.connect(self.select_all)
        btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("☐ 선택 해제")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(deselect_all_btn)
        
        btn_layout.addStretch()
        
        # 폴더 다운로드 방식 선택
        btn_layout.addWidget(QLabel("폴더 저장:"))
        self.folder_mode_combo = QComboBox()
        self.folder_mode_combo.addItems(["압축(더빠름)", "폴더 그대로"])
        # 저장된 설정 불러오기
        saved_mode = self.settings.get('folder_download_mode', 'zip')
        self.folder_mode_combo.setCurrentIndex(0 if saved_mode == 'zip' else 1)
        self.folder_mode_combo.currentIndexChanged.connect(self.on_folder_mode_changed)
        btn_layout.addWidget(self.folder_mode_combo)
        
        # 중복 파일 처리 방식
        btn_layout.addWidget(QLabel("중복:"))
        self.duplicate_mode_combo = QComboBox()
        self.duplicate_mode_combo.addItems(["덮어쓰기", "번호 추가"])
        saved_dup_mode = self.settings.get('duplicate_mode', 'overwrite')
        self.duplicate_mode_combo.setCurrentIndex(0 if saved_dup_mode == 'overwrite' else 1)
        self.duplicate_mode_combo.currentIndexChanged.connect(self.on_duplicate_mode_changed)
        btn_layout.addWidget(self.duplicate_mode_combo)
        
        layout.addWidget(btn_widget)
        
        # 다운로드 진행 영역
        download_area_label = QLabel("다운로드 진행")
        download_area_label.setFont(QFont("맑은 고딕", 10, QFont.Bold))
        download_area_label.setContentsMargins(5, 5, 5, 2)
        layout.addWidget(download_area_label)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(150)
        scroll.setMaximumHeight(150)
        
        self.download_container = QWidget()
        self.download_layout = QVBoxLayout(self.download_container)
        self.download_layout.setContentsMargins(0, 0, 0, 0)
        self.download_layout.setSpacing(2)
        self.download_layout.addStretch()
        
        scroll.setWidget(self.download_container)
        layout.addWidget(scroll)
        
        # 로그 영역 - 접기/펼치기
        log_header_widget = QWidget()
        log_header_layout = QHBoxLayout(log_header_widget)
        log_header_layout.setContentsMargins(5, 5, 5, 2)
        
        self.log_toggle_btn = QPushButton("▶ 로그")
        self.log_toggle_btn.setFont(QFont("맑은 고딕", 9, QFont.Bold))
        self.log_toggle_btn.setFlat(True)
        self.log_toggle_btn.setStyleSheet("text-align: left; padding: 2px;")
        self.log_toggle_btn.clicked.connect(self.toggle_log)
        log_header_layout.addWidget(self.log_toggle_btn)
        log_header_layout.addStretch()
        
        layout.addWidget(log_header_widget)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(80)
        self.log_text.setVisible(False)  # 기본적으로 숨김
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00ff00;
                border: 1px solid #333333;
                font-family: 'Consolas', monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 상태바
        self.statusbar = QLabel(f"다운로드 폴더: {self.download_dir}")
        self.statusbar.setStyleSheet("padding: 5px; background-color: #1a1a1a;")
        layout.addWidget(self.statusbar)
        
        # 공유 폴더 로드
        self.load_shared_folders()
    
    def toggle_log(self):
        """로그 표시/숨김 토글"""
        is_visible = self.log_text.isVisible()
        self.log_text.setVisible(not is_visible)
        
        if is_visible:
            self.log_toggle_btn.setText("▶ 로그")
        else:
            self.log_toggle_btn.setText("▼ 로그")
    
    def add_log(self, message):
        """로그 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def load_shared_folders(self):
        """공유 폴더 목록 로드"""
        try:
            self.add_log("공유 폴더 목록 로드 중...")
            response = self.session.get(f"{self.server_url}/api/shared_folders", timeout=10)
            if response.status_code == 200:
                folders = response.json().get('folders', [])
                if folders:
                    self.add_log(f"공유 폴더 발견: {len(folders)}개")
                    self.browse(folders[0])
        except Exception as e:
            self.add_log(f"❌ 오류: {e}")
            QMessageBox.critical(self, "오류", f"공유 폴더 로드 실패:\n{e}")
    
    def browse(self, path):
        """폴더 탐색"""
        self.current_path = path
        self.path_label.setText(path)
        
        try:
            response = self.session.get(f"{self.server_url}/api/files",
                                       params={'path': path}, timeout=10)
            if response.status_code == 200:
                files = response.json().get('files', [])
                self.populate_tree(files)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"폴더 로드 실패:\n{e}")
    
    def populate_tree(self, files):
        """트리 채우기"""
        self.file_tree.clear()
        
        for file_info in sorted(files, key=lambda x: (not x['is_dir'], x['name'].lower())):
            item = QTreeWidgetItem()
            
            # 체크박스
            item.setCheckState(0, Qt.Unchecked)
            
            # 아이콘 + 이름
            icon = "📁 " if file_info['is_dir'] else "📄 "
            item.setText(1, icon + file_info['name'])
            
            # 수정일
            try:
                modified = datetime.fromtimestamp(file_info['modified']).strftime("%Y-%m-%d %H:%M")
                item.setText(2, modified)
            except:
                item.setText(2, "")
            
            # 데이터 저장
            item.setData(0, Qt.UserRole, file_info['path'])
            item.setData(1, Qt.UserRole, "dir" if file_info['is_dir'] else "file")
            
            self.file_tree.addTopLevelItem(item)
    
    def on_item_clicked(self, item, column):
        """항목 클릭 - 체크박스 클릭 시 선택된 모든 항목 체크"""
        if column == 0:  # 체크박스 컬럼
            selected_items = self.file_tree.selectedItems()
            if len(selected_items) > 1:
                # 여러 항목이 선택된 경우, 클릭한 항목의 체크 상태로 모두 변경
                new_state = item.checkState(0)
                for selected_item in selected_items:
                    selected_item.setCheckState(0, new_state)
        else:
            # 다른 컬럼 클릭 시에도 여러 항목 선택 상태면 체크박스 클릭처럼 작동
            selected_items = self.file_tree.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                # 현재 항목의 반대 상태로 모두 변경
                current_state = item.checkState(0)
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                for selected_item in selected_items:
                    selected_item.setCheckState(0, new_state)
    
    def on_item_double_clicked(self, item, column):
        """항목 더블클릭"""
        item_type = item.data(1, Qt.UserRole)
        if item_type == "dir":
            path = item.data(0, Qt.UserRole)
            self.browse(path)
    
    def go_back(self):
        """뒤로 가기"""
        if self.current_path:
            parent = os.path.dirname(self.current_path)
            if parent:
                self.browse(parent)
    
    def refresh(self):
        """새로고침"""
        if self.current_path:
            self.browse(self.current_path)
    
    def select_all(self):
        """전체 선택"""
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)
    
    def deselect_all(self):
        """전체 해제"""
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
    
    def on_folder_mode_changed(self, index):
        """폴더 다운로드 방식 변경"""
        mode = 'zip' if index == 0 else 'extract'
        self.settings['folder_download_mode'] = mode
        self.save_settings()
        self.add_log(f"폴더 저장 방식: {self.folder_mode_combo.currentText()}")
    
    def on_duplicate_mode_changed(self, index):
        """중복 파일 처리 방식 변경"""
        mode = 'overwrite' if index == 0 else 'rename'
        self.settings['duplicate_mode'] = mode
        self.save_settings()
        self.add_log(f"중복 파일 처리: {self.duplicate_mode_combo.currentText()}")
    
    def open_download_folder(self):
        """다운로드 폴더 열기"""
        try:
            if os.path.exists(self.download_dir):
                os.startfile(self.download_dir)
            else:
                os.makedirs(self.download_dir, exist_ok=True)
                os.startfile(self.download_dir)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"폴더 열기 실패:\n{e}")
    
    def set_download_path(self):
        """다운로드 경로 설정"""
        new_path = QFileDialog.getExistingDirectory(
            self, 
            "다운로드 폴더 선택", 
            self.download_dir
        )
        
        if new_path:
            self.download_dir = new_path
            self.settings['download_dir'] = new_path
            self.save_settings()
            QMessageBox.information(self, "경로 변경", f"다운로드 폴더가 변경되었습니다:\n{new_path}")
    
    def on_item_clicked(self, item, column):
        """항목 클릭 - 체크박스 클릭 시 선택된 모든 항목 체크"""
        if column == 0:  # 체크박스 컬럼
            selected_items = self.file_tree.selectedItems()
            if len(selected_items) > 1:
                # 여러 항목이 선택된 경우, 클릭한 항목의 체크 상태로 모두 변경
                new_state = item.checkState(0)
                for selected_item in selected_items:
                    selected_item.setCheckState(0, new_state)
        else:
            # 다른 컬럼 클릭 시에도 여러 항목 선택 상태면 체크박스 클릭처럼 작동
            selected_items = self.file_tree.selectedItems()
            if len(selected_items) > 1 and item in selected_items:
                # 현재 항목의 반대 상태로 모두 변경
                current_state = item.checkState(0)
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                for selected_item in selected_items:
                    selected_item.setCheckState(0, new_state)
    
    def on_item_double_clicked(self, item, column):
        """항목 더블클릭"""
        item_type = item.data(1, Qt.UserRole)
        if item_type == "dir":
            path = item.data(0, Qt.UserRole)
            self.browse(path)
    
    def go_back(self):
        """뒤로 가기"""
        if self.current_path:
            parent = os.path.dirname(self.current_path)
            if parent:
                self.browse(parent)
    
    def refresh(self):
        """새로고침"""
        if self.current_path:
            self.browse(self.current_path)
    
    def select_all(self):
        """전체 선택"""
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)
    
    def deselect_all(self):
        """전체 해제"""
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
    
    def on_folder_mode_changed(self, index):
        """폴더 다운로드 방식 변경"""
        mode = 'zip' if index == 0 else 'extract'
        self.settings['folder_download_mode'] = mode
        self.save_settings()
        self.add_log(f"폴더 저장 방식: {self.folder_mode_combo.currentText()}")
    
    def on_duplicate_mode_changed(self, index):
        """중복 파일 처리 방식 변경"""
        mode = 'overwrite' if index == 0 else 'rename'
        self.settings['duplicate_mode'] = mode
        self.save_settings()
        self.add_log(f"중복 파일 처리: {self.duplicate_mode_combo.currentText()}")
    
    def open_download_folder(self):
        """다운로드 폴더 열기"""
        try:
            if os.path.exists(self.download_dir):
                os.startfile(self.download_dir)
            else:
                os.makedirs(self.download_dir, exist_ok=True)
                os.startfile(self.download_dir)
        except Exception as e:
            QMessageBox.critical(self, "오류", f"폴더 열기 실패:\n{e}")
    
    def set_download_path(self):
        """다운로드 경로 설정"""
        new_path = QFileDialog.getExistingDirectory(
            self, 
            "다운로드 폴더 선택", 
            self.download_dir
        )
            
        if new_path:
            self.download_dir = new_path
            self.settings['download_dir'] = new_path
            self.save_settings()
            QMessageBox.information(self, "경로 변경", f"다운로드 폴더가 변경되었습니다:\n{new_path}")
    
    def upload_files(self):
        """파일 또는 폴더 업로드"""
        if not self.current_path:
            QMessageBox.warning(self, "경고", "업로드할 위치를 먼저 선택하세요.")
            return
        
        # 단일 비네이티브 다이얼로그에서 파일/폴더 동시 선택 지원
        dialog = QFileDialog(self, "업로드할 파일/폴더 선택")
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.ReadOnly, True)
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setNameFilter("모든 파일 (*)")
        
        # 비네이티브 다이얼로그에서 디렉터리도 다중 선택 가능하도록 뷰 설정
        for view in dialog.findChildren((QListView, QTreeView)):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        if dialog.exec_():
            paths = dialog.selectedFiles()
            if not paths:
                return
            for path in paths:
                if os.path.isdir(path):
                    self.upload_folder(path, self.current_path)
                else:
                    self.upload_single_file(path, self.current_path)

    def upload_files_only(self):
        """파일 업로드(네이티브 파일 선택창)"""
        if not self.current_path:
            QMessageBox.warning(self, "경고", "업로드할 위치를 먼저 선택하세요.")
            return
        file_paths, _ = QFileDialog.getOpenFileNames(self, "업로드할 파일 선택")
        if not file_paths:
            return
        for path in file_paths:
            if os.path.isdir(path):
                # 사용자가 폴더를 선택했을 가능성 대비
                self.upload_folder(path, self.current_path)
            else:
                self.upload_single_file(path, self.current_path)

    def upload_folder_only(self):
        """폴더 업로드(네이티브 폴더 선택창)"""
        if not self.current_path:
            QMessageBox.warning(self, "경고", "업로드할 위치를 먼저 선택하세요.")
            return
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "업로드할 폴더 선택",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if folder_path:
            self.upload_folder(folder_path, self.current_path)
    
    def upload_folder(self, folder_path, target_folder):
        """폴더 업로드 (폴더 구조 유지하며 실시간 업로드)"""
        folder_name = os.path.basename(folder_path)
        self.add_log(f"📤 폴더 업로드 시작: {folder_name}")
        
        # 폴더 내 모든 파일 찾기
        file_list = []
        total_bytes = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_full_path = os.path.join(root, file)
                # 폴더 구조 유지를 위한 상대 경로 계산
                relative_path = os.path.relpath(file_full_path, folder_path)
                # 폴더 이름을 포함한 상대 경로
                relative_with_folder = os.path.join(folder_name, relative_path)
                file_list.append((file_full_path, relative_with_folder))
                try:
                    total_bytes += os.path.getsize(file_full_path)
                except Exception:
                    pass
        
        if not file_list:
            QMessageBox.information(self, "정보", "업로드할 파일이 없습니다.")
            return
        
        self.add_log(f"총 {len(file_list)}개 파일 업로드 예정")
        
        # 배치 ID와 집계 위젯 생성
        batch_id = str(int(time.time() * 1000))
        self.upload_batches[batch_id] = {
            'total': total_bytes,
            'uploaded': 0,
            'pending': len(file_list)
        }
        # 배치 진행 표시용 위젯 추가
        batch_task = UploadTask(folder_path, target_folder, folder_name)
        batch_widget = DownloadItemWidget(batch_task)
        batch_widget.name_label.setText(f"⬆️ 폴더 전체: {folder_name}")
        batch_widget.pause_btn.setVisible(False)
        batch_widget.cancel_btn.setVisible(False)
        self.download_layout.insertWidget(self.download_layout.count() - 1, batch_widget)
        self.upload_batch_widgets[batch_id] = batch_widget
        
        # 업로드 큐 초기화
        if not hasattr(self, 'upload_queue'):
            self.upload_queue = []
        if not hasattr(self, 'active_uploads'):
            self.active_uploads = 0
        
        # 모든 파일을 큐에 추가
        for file_path, relative_path in file_list:
            task = UploadTask(file_path, target_folder, relative_path)
            task.batch_id = batch_id
            self.upload_queue.append(task)
        
        # 큐 처리 시작
        self.process_upload_queue()
    
    def upload_single_file(self, file_path, target_folder):
        """단일 파일 업로드"""
        file_name = os.path.basename(file_path)
        self.add_log(f"📤 파일 업로드 시작: {file_name}")
        
        # 큐 초기화
        if not hasattr(self, 'upload_queue'):
            self.upload_queue = []
        if not hasattr(self, 'active_uploads'):
            self.active_uploads = 0
        
        task = UploadTask(file_path, target_folder, '')
        self.upload_queue.append(task)
        self.process_upload_queue()
    
    def process_upload_queue(self):
        """업로드 큐 처리 (최대 3개 동시 업로드)"""
        MAX_CONCURRENT_UPLOADS = 3
        
        if not hasattr(self, 'upload_queue'):
            self.upload_queue = []
        if not hasattr(self, 'active_uploads'):
            self.active_uploads = 0
        
        # 큐에서 작업을 꺼내서 시작
        while self.upload_queue and self.active_uploads < MAX_CONCURRENT_UPLOADS:
            task = self.upload_queue.pop(0)
            self.active_uploads += 1
            self.start_upload_task(task)
    
    def start_upload_task(self, task):
        """업로드 작업 시작"""
        if not hasattr(self, 'upload_tasks'):
            self.upload_tasks = []
        if not hasattr(self, 'upload_widgets'):
            self.upload_widgets = {}
        
        self.upload_tasks.append(task)
        
        # UI 추가
        widget = DownloadItemWidget(task)  # DownloadItemWidget을 업로드에도 재사용
        widget.name_label.setText(f"⬆️ {task.file_name}")
        widget.cancel_btn.clicked.connect(lambda checked, t=task: self.cancel_upload(t))
        widget.pause_btn.setVisible(False)  # 업로드는 일시정지 불가
        
        self.download_layout.insertWidget(self.download_layout.count() - 1, widget)
        self.upload_widgets[id(task)] = widget
        
        # 업로드 시작
        thread = UploadThread(task, self.server_url, self.session)
        thread.progress.connect(lambda p, s, u, t, w=widget, task_ref=task: self.update_upload_progress(w, p, s, u, t, task_ref))
        thread.finished.connect(lambda success, msg, w=widget, t=task: self.upload_finished(w, t, success, msg))
        
        # 스레드를 멤버로 저장 (GC 방지)
        if not hasattr(self, 'upload_threads'):
            self.upload_threads = []
        self.upload_threads.append(thread)
        thread.finished.connect(lambda: self.upload_threads.remove(thread) if thread in self.upload_threads else None)
        
        thread.start()
    
    def update_upload_progress(self, widget, percent, speed_text, uploaded, total, task):
        """업로드 진행률 업데이트"""
        widget.progress_bar.setValue(percent)
        
        # 크기 포맷
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        
        uploaded_str = format_size(uploaded)
        total_str = format_size(total)
        
        widget.status_label.setText(f"{percent}% - {speed_text} - {uploaded_str} / {total_str}")

        # 배치(폴더 전체) 진행 집계
        batch_id = getattr(task, 'batch_id', None)
        if batch_id and batch_id in self.upload_batches:
            batch = self.upload_batches[batch_id]
            # 증분 반영
            delta = max(0, uploaded - getattr(task, 'last_reported', 0))
            task.last_reported = uploaded
            batch['uploaded'] = min(batch['total'], batch['uploaded'] + delta)
            # 배치 위젯 업데이트
            self.update_batch_progress(batch_id)
    
    def upload_finished(self, widget, task, success, message):
        """업로드 완료 처리"""
        # 활성 업로드 수 감소
        if hasattr(self, 'active_uploads'):
            self.active_uploads = max(0, self.active_uploads - 1)
        
        # 다음 큐 항목 처리
        self.process_upload_queue()
        
        if success:
            widget.status_label.setText("✓ 업로드 완료")
            widget.progress_bar.setValue(100)
            self.add_log(f"✓ 업로드 완료: {task.file_name}")
            
            # 완료된 항목은 즉시 제거 (버튼 숨김 처리)
            widget.pause_btn.setVisible(False)
            widget.cancel_btn.setVisible(False)

            # 페이드 아웃 후 제거
            QTimer.singleShot(200, lambda: self.fade_out_upload_widget(widget, task))
            
            # 업로드 완료 후 폴더 새로고침
            QTimer.singleShot(500, self.refresh)
        else:
            widget.status_label.setText(f"✕ {message}")
            self.add_log(f"❌ 업로드 실패: {task.file_name} - {message}")
            widget.cancel_btn.setEnabled(False)

        # 배치(폴더 전체) 완료 여부 갱신
        batch_id = getattr(task, 'batch_id', None)
        if batch_id and batch_id in self.upload_batches:
            batch = self.upload_batches[batch_id]
            # 누락된 잔여 바이트 반영
            remaining = task.total_size - getattr(task, 'last_reported', 0)
            if remaining > 0:
                batch['uploaded'] = min(batch['total'], batch['uploaded'] + remaining)
                task.last_reported = task.total_size
            # 대기 파일 수 감소
            batch['pending'] = max(0, batch.get('pending', 0) - 1)
            self.update_batch_progress(batch_id)
            # 배치 완료 시 정리
            if batch['pending'] == 0 or batch['uploaded'] >= batch['total']:
                self.finish_batch(batch_id)

    def update_batch_progress(self, batch_id):
        """배치(폴더 전체) 진행 위젯 업데이트"""
        if batch_id not in self.upload_batches or batch_id not in self.upload_batch_widgets:
            return
        batch = self.upload_batches[batch_id]
        widget = self.upload_batch_widgets[batch_id]
        total = max(1, batch['total'])
        percent = int((batch['uploaded'] / total) * 100)

        # 크기 포맷
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"

        widget.progress_bar.setValue(percent)
        widget.status_label.setText(f"{percent}% - 전체 {format_size(batch['uploaded'])} / {format_size(batch['total'])}")

    def finish_batch(self, batch_id):
        """배치(폴더 전체) 완료 처리 및 위젯 제거"""
        if batch_id not in self.upload_batches or batch_id not in self.upload_batch_widgets:
            return
        widget = self.upload_batch_widgets[batch_id]
        widget.progress_bar.setValue(100)
        widget.status_label.setText("✓ 폴더 전체 업로드 완료")

        # 페이드 아웃 후 제거
        def _remove():
            if hasattr(self, 'download_layout'):
                self.download_layout.removeWidget(widget)
            widget.deleteLater()
            self.upload_batch_widgets.pop(batch_id, None)
            self.upload_batches.pop(batch_id, None)

        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(1200)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        if not hasattr(self, 'animations'):
            self.animations = []
        self.animations.append(animation)
        animation.finished.connect(lambda: self.animations.remove(animation) if animation in self.animations else None)
        animation.finished.connect(_remove)
        animation.start()
    
    def fade_out_upload_widget(self, widget, task):
        """업로드 위젯 페이드 아웃"""
        task_id = id(task)
        if task_id not in self.upload_widgets:
            return
        
        # 페이드 아웃 효과
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(1200)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.finished.connect(lambda: self.remove_upload_widget(widget, task))
        
        if not hasattr(self, 'animations'):
            self.animations = []
        self.animations.append(animation)
        animation.finished.connect(lambda: self.animations.remove(animation) if animation in self.animations else None)
        
        animation.start()
    
    def remove_upload_widget(self, widget, task):
        """업로드 위젯 제거"""
        self.download_layout.removeWidget(widget)
        widget.deleteLater()
        if id(task) in self.upload_widgets:
            del self.upload_widgets[id(task)]
        if hasattr(self, 'upload_tasks') and task in self.upload_tasks:
            self.upload_tasks.remove(task)
    
    def cancel_upload(self, task):
        """업로드 취소"""
        reply = QMessageBox.question(
            self,
            '업로드 취소',
            f'{task.file_name}\n업로드를 취소하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            task.cancel_flag = True
            task.status = 'cancelled'
            
            task_id = id(task)
            if task_id in self.upload_widgets:
                widget = self.upload_widgets[task_id]
                widget.status_label.setText("✕ 취소됨")
                widget.cancel_btn.setEnabled(False)
                QTimer.singleShot(1500, lambda: self.fade_out_upload_widget(widget, task))
    
    def download_selected(self):
        """선택 항목 다운로드"""
        checked_items = []
        for i in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                checked_items.append(item)
        
        if not checked_items:
            QMessageBox.warning(self, "경고", "다운로드할 항목을 선택하세요.")
            return
        
        download_path = QFileDialog.getExistingDirectory(self, "다운로드 위치", self.download_dir)
        if not download_path:
            return
        
        for item in checked_items:
            file_path = item.data(0, Qt.UserRole)
            item_type = item.data(1, Qt.UserRole)
            file_name_with_icon = item.text(1)
            # 아이콘 제거 (첫 2-3 문자)
            file_name = file_name_with_icon.lstrip("📁📄 ")
            
            is_folder = (item_type == "dir")
            
            # 폴더 다운로드 방식에 따라 처리
            folder_mode = self.settings.get('folder_download_mode', 'zip')
            if is_folder:
                if folder_mode == 'zip':
                    # ZIP으로 저장
                    save_name = file_name + ".zip"
                    download_as_zip = True
                    auto_extract = False
                else:
                    # 폴더 그대로 (다운로드 후 압축 해제)
                    save_name = file_name + ".zip"  # 임시로 ZIP 다운로드
                    download_as_zip = True
                    auto_extract = True
            else:
                save_name = file_name
                download_as_zip = False
                auto_extract = False
            
            save_path = os.path.join(download_path, save_name)
            
            # 중복 파일 처리
            duplicate_mode = self.settings.get('duplicate_mode', 'overwrite')
            if os.path.exists(save_path) and duplicate_mode == 'rename':
                # 번호 추가 방식
                base_name, ext = os.path.splitext(save_name)
                counter = 1
                while os.path.exists(save_path):
                    new_name = f"{base_name} ({counter}){ext}"
                    save_path = os.path.join(download_path, new_name)
                    counter += 1
                save_name = os.path.basename(save_path)
            
            task = DownloadTask(file_path, save_name, save_path, 0)
            task.auto_extract = auto_extract  # 압축 해제 플래그
            task.is_folder = is_folder       # 폴더 다운로드 여부 플래그
            self.download_tasks.append(task)
            
            if auto_extract:
                self.add_log(f"📥 다운로드 시작: {file_name} (폴더 그대로)")
            else:
                self.add_log(f"📥 다운로드 시작: {save_name}")
            
            # UI 추가
            widget = DownloadItemWidget(task)
            widget.cancel_btn.clicked.connect(lambda checked, t=task: self.cancel_download(t))
            widget.pause_btn.clicked.connect(lambda checked, t=task: self.pause_download(t))
            
            self.download_layout.insertWidget(self.download_layout.count() - 1, widget)
            self.download_widgets[id(task)] = widget
            
            # 다운로드 시작 (ZIP 다운로드 여부 전달)
            thread = DownloadThread(task, self.server_url, self.session, download_as_zip)
            thread.progress.connect(lambda p, s, d, t, w=widget: self.update_progress(w, p, s, d, t))
            thread.finished.connect(lambda success, msg, w=widget, t=task: self.download_finished(w, t, success, msg))
            
            # 스레드를 멤버로 저장 (GC 방지)
            if not hasattr(self, 'download_threads'):
                self.download_threads = []
            self.download_threads.append(thread)
            thread.finished.connect(lambda: self.download_threads.remove(thread) if thread in self.download_threads else None)
            
            self.has_active_downloads = True
            thread.start()
    
    def update_progress(self, widget, percent, speed_text, downloaded, total):
        """진행률 업데이트"""
        widget.progress_bar.setValue(percent)
        
        # 크기 포맷
        def format_size(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        
        downloaded_str = format_size(downloaded)
        total_str = format_size(total)
        
        widget.status_label.setText(f"{percent}% - {speed_text} - {downloaded_str} / {total_str}")
    
    def download_finished(self, widget, task, success, message):
        """다운로드 완료"""
        # 이미 취소 처리 중이면 무시
        if task.status == 'cancelled' and message == "취소됨":
            return
        
        if success:
            # 최종 용량 계산 (폴더 자동 해제 시 폴더 용량, 그렇지 않으면 파일 용량)
            def get_dir_size(path):
                total = 0
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            total += os.path.getsize(fp)
                        except Exception:
                            pass
                return total

            def format_size(size):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.1f} {unit}"
                    size /= 1024.0
                return f"{size:.1f} TB"

            if getattr(task, 'auto_extract', False) and getattr(task, 'is_folder', False) and task.save_path.endswith('.zip'):
                final_path = task.save_path[:-4]
                final_bytes = get_dir_size(final_path) if os.path.exists(final_path) else 0
            else:
                final_path = task.save_path
                try:
                    final_bytes = os.path.getsize(final_path)
                except Exception:
                    final_bytes = 0

            widget.progress_bar.setValue(100)
            widget.progress_bar.setVisible(False)  # 완료 후 진행바 숨김
            widget.status_label.setText(f"✓ 완료 - 최종 용량: {format_size(final_bytes)}")
            self.add_log(f"✓ 완료: {task.file_name} ({format_size(final_bytes)})")
            
            # 완료 시 일시정지 버튼 숨기고 취소 버튼을 "완료"(✓) 버튼으로 변경
            widget.pause_btn.setVisible(False)
            widget.cancel_btn.setText("✓")
            widget.cancel_btn.setFixedSize(30, 30)
            widget.cancel_btn.setObjectName("completeBtn")
            widget.cancel_btn.setStyleSheet("""
                QPushButton#completeBtn {
                    background-color: #10b981;
                    color: #ffffff;
                }
                QPushButton#completeBtn:hover {
                    background-color: #059669;
                }
            """)
            # 버튼 클릭 시 제거
            widget.cancel_btn.clicked.disconnect()
            widget.cancel_btn.clicked.connect(lambda: self.fade_out_widget(widget, task))
        else:
            widget.status_label.setText(f"✕ {message}")
            self.add_log(f"❌ 실패: {task.file_name} - {message}")
            widget.pause_btn.setEnabled(False)
            widget.cancel_btn.setEnabled(False)
    
    def fade_out_widget(self, widget, task, slow=False):
        """위젯 페이드 아웃"""
        # 중복 방지
        task_id = id(task)
        if task_id not in self.download_widgets:
            return
        
        # QGraphicsOpacityEffect 사용 (일반 위젯에서 작동)
        opacity_effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(opacity_effect)
        
        # 애니메이션 효과
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        if slow:
            animation.setDuration(2500)  # 취소 시 2.5초로 아주 느리게
        else:
            animation.setDuration(1200)  # 완료 시 1.2초
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.finished.connect(lambda: self.remove_download_widget(widget, task))
        
        # 애니메이션을 멤버로 저장 (GC 방지)
        if not hasattr(self, 'animations'):
            self.animations = []
        self.animations.append(animation)
        animation.finished.connect(lambda: self.animations.remove(animation) if animation in self.animations else None)
        
        animation.start()
    
    def remove_download_widget(self, widget, task):
        """다운로드 위젯 제거"""
        self.download_layout.removeWidget(widget)
        widget.deleteLater()
        if id(task) in self.download_widgets:
            del self.download_widgets[id(task)]
        if task in self.download_tasks:
            self.download_tasks.remove(task)
        
        # 활성 다운로드 체크
        self.has_active_downloads = any(
            t.status in ['downloading', 'waiting'] 
            for t in self.download_tasks
        )
    
    def pause_download(self, task):
        """다운로드 일시정지/재개"""
        if task.status == 'downloading':
            task.pause_flag = True
            task.status = 'paused'
        elif task.status == 'paused':
            task.pause_flag = False
            task.status = 'downloading'
    
    def cancel_download(self, task):
        """다운로드 취소"""
        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            '다운로드 취소',
            f'{task.file_name}\n다운로드를 취소하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            task.cancel_flag = True
            task.status = 'cancelled'
            
            # 취소 시에도 페이드 아웃 (더 천천히)
            task_id = id(task)
            if task_id in self.download_widgets:
                widget = self.download_widgets[task_id]
                widget.status_label.setText("✕ 취소됨")
                widget.pause_btn.setEnabled(False)
                widget.cancel_btn.setEnabled(False)
                QTimer.singleShot(1500, lambda: self.fade_out_widget(widget, task, slow=True))
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        reply = QMessageBox.question(
            self,
            '종료 확인',
            '프로그램을 종료하시겠습니까?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 진행 중인 다운로드 취소
            for task in self.download_tasks:
                task.cancel_flag = True
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    
    window = FileShareClient()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
