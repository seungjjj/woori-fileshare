"""
통합 파일 공유 서버 - PyQt5 모던 버전
모든 기능을 하나로: 서버 + 터널 + 시스템 트레이
"""
import sys
import os
import json
import threading
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox,
    QFileDialog, QTextEdit, QGroupBox, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PIL import Image, ImageDraw
import pystray

# 로컬 모듈
from cloudflared_manager import CloudflaredManager

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
}

QPushButton {
    background-color: #ffffff;
    color: #000000;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #e0e0e0;
}

QPushButton:disabled {
    background-color: #333333;
    color: #666666;
}

QListWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #2563eb;
}

QGroupBox {
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    margin-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 5px 10px;
}

QTextEdit {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
}

QPushButton#startBtn {
    background-color: #10b981;
    color: #ffffff;
    font-size: 14pt;
    padding: 15px;
}

QPushButton#startBtn:hover {
    background-color: #059669;
}

QPushButton#stopBtn {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#stopBtn:hover {
    background-color: #ef4444;
}
"""


class ServerThread(QThread):
    """서버 시작 스레드"""
    status_update = pyqtSignal(str, str)  # 메시지, 색상
    tunnel_created = pyqtSignal(str)  # 터널 URL
    error_occurred = pyqtSignal(str)  # 에러 메시지
    
    def __init__(self, users, shared_folders, tunnel_manager):
        super().__init__()
        self.users = users
        self.shared_folders = shared_folders
        self.tunnel_manager = tunnel_manager
    
    def run(self):
        try:
            from werkzeug.security import generate_password_hash
            import server as server_module
            
            # 서버 모듈 설정
            print("\n[DEBUG] 서버 시작 - 사용자 설정:")
            for username, password in self.users.items():
                print(f"  사용자: {username}, 비밀번호: {password}")
            
            server_module.USERS = {username: generate_password_hash(password) 
                                   for username, password in self.users.items()}
            server_module.SHARED_FOLDERS = self.shared_folders.copy()
            server_module.ACCESS_CODE = "UNIFIED"
            
            print(f"[DEBUG] 설정된 사용자 수: {len(server_module.USERS)}")
            print(f"[DEBUG] 공유 폴더 수: {len(server_module.SHARED_FOLDERS)}")
            
            self.status_update.emit("Flask 서버 시작 중...", "blue")
            
            # Flask 서버를 별도 스레드에서 시작
            def run_flask():
                try:
                    if getattr(sys, 'frozen', False):
                        try:
                            from waitress import serve
                            serve(server_module.app, listen='127.0.0.1:5000', threads=32)
                        except ImportError:
                            server_module.app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
                    else:
                        server_module.app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
                except Exception as e:
                    self.error_occurred.emit(f"Flask 서버 시작 실패: {e}")
            
            flask_thread = threading.Thread(target=run_flask, daemon=True)
            flask_thread.start()
            
            # Flask가 시작될 때까지 잠시 대기
            import time
            time.sleep(2)
            
            self.status_update.emit("Cloudflared 터널 생성 중...", "blue")
            
            # Cloudflared 터널 시작
            def tunnel_status(msg):
                self.status_update.emit(msg, "blue")
            
            tunnel_url = self.tunnel_manager.start_tunnel(5000, tunnel_status)
            
            if tunnel_url:
                self.tunnel_created.emit(tunnel_url)
            else:
                self.error_occurred.emit(
                    "터널 생성에 실패했습니다.\n\n"
                    "Cloudflared를 다운로드할 수 없거나\n"
                    "네트워크 연결에 문제가 있을 수 있습니다.")
        
        except Exception as e:
            self.error_occurred.emit(f"서버 시작 실패:\n{e}")


class AddUserDialog(QDialog):
    """사용자 추가 대화상자"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용자 추가")
        self.setFixedSize(400, 180)
        
        layout = QVBoxLayout(self)
        
        # 아이디
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("아이디:"))
        self.username_entry = QLineEdit()
        id_layout.addWidget(self.username_entry)
        layout.addLayout(id_layout)
        
        # 비밀번호
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("비밀번호:"))
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        pw_layout.addWidget(self.password_entry)
        layout.addLayout(pw_layout)
        
        # 버튼
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.username_entry.setFocus()


class UnifiedFileShareServer(QMainWindow):
    """PyQt5 통합 파일 공유 서버"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("파일 공유 서버 - PyQt5")
        self.resize(750, 700)
        
        # 화면 중앙 배치
        self.center_on_screen()
        
        # 설정 파일 경로
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(base_dir, "unified_server_config_pyqt.json")
        
        self.shared_folders = []
        self.users = {}
        self.server_thread = None
        self.server_running = False
        
        # Cloudflared 터널 매니저
        self.tunnel_manager = CloudflaredManager()
        self.tunnel_url = None
        
        # 시스템 트레이
        self.tray_icon = None
        
        # 설정 로드
        self.load_config()
        
        # GUI 생성
        self.create_setup_screen()
    
    def center_on_screen(self):
        """화면 중앙에 배치"""
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def load_config(self):
        """설정 불러오기"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.users = config.get('users', {})
                    self.shared_folders = config.get('shared_folders', [])
        except Exception as e:
            print(f"설정 불러오기 실패: {e}")
    
    def save_config(self):
        """설정 저장"""
        try:
            config = {
                'users': self.users,
                'shared_folders': self.shared_folders
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"설정 저장 실패: {e}")
    
    def create_setup_screen(self):
        """서버 설정 화면"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 제목
        title = QLabel("🚀 통합 파일 공유 서버")
        title.setFont(QFont("맑은 고딕", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        desc = QLabel("모든 기능이 하나로! 설정하고 시작 버튼만 누르세요")
        desc.setFont(QFont("맑은 고딕", 10))
        desc.setStyleSheet("color: #999999;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        # 사용자 계정 섹션
        user_group = QGroupBox("👤 사용자 계정 (클라이언트 로그인용)")
        user_layout = QVBoxLayout(user_group)
        
        self.user_list = QListWidget()
        self.user_list.setMaximumHeight(100)
        user_layout.addWidget(self.user_list)
        
        user_btn_layout = QHBoxLayout()
        add_user_btn = QPushButton("➕ 계정 추가")
        add_user_btn.clicked.connect(self.add_user_dialog)
        user_btn_layout.addWidget(add_user_btn)
        
        remove_user_btn = QPushButton("➖ 계정 제거")
        remove_user_btn.clicked.connect(self.remove_user)
        user_btn_layout.addWidget(remove_user_btn)
        
        user_layout.addLayout(user_btn_layout)
        layout.addWidget(user_group)
        
        # 공유 폴더 섹션
        folder_group = QGroupBox("📁 공유 폴더")
        folder_layout = QVBoxLayout(folder_group)
        
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(120)
        folder_layout.addWidget(self.folder_list)
        
        folder_btn_layout = QHBoxLayout()
        add_folder_btn = QPushButton("📁 폴더 추가")
        add_folder_btn.clicked.connect(self.add_folder)
        folder_btn_layout.addWidget(add_folder_btn)
        
        remove_folder_btn = QPushButton("➖ 폴더 제거")
        remove_folder_btn.clicked.connect(self.remove_folder)
        folder_btn_layout.addWidget(remove_folder_btn)
        
        folder_layout.addLayout(folder_btn_layout)
        layout.addWidget(folder_group)
        
        # 상태 표시
        status_group = QGroupBox("📊 상태")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("준비됨")
        self.status_label.setFont(QFont("맑은 고딕", 11))
        self.status_label.setStyleSheet("color: #2563eb;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(status_group)
        
        # 서버 시작 버튼
        self.start_btn = QPushButton("🚀 서버 시작 (원거리 접속 자동)")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setFont(QFont("맑은 고딕", 14, QFont.Bold))
        self.start_btn.setMinimumHeight(60)
        self.start_btn.clicked.connect(self.start_unified_server)
        layout.addWidget(self.start_btn)
        
        info = QLabel("💡 시작하면 자동으로 원거리 접속 키(URL)가 생성됩니다\n"
                     "최소화하면 시스템 트레이에서 백그라운드 실행됩니다")
        info.setStyleSheet("color: #999999;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        layout.addStretch()
        
        # 초기 데이터 표시
        self.refresh_user_list()
        self.refresh_folder_list()
        
        # 기본 계정 추가 (처음 실행 시)
        if not self.users:
            self.users['admin'] = 'admin'
            self.save_config()
            self.refresh_user_list()
    
    def refresh_user_list(self):
        """사용자 목록 새로고침"""
        self.user_list.clear()
        for username in self.users.keys():
            self.user_list.addItem(username)
    
    def refresh_folder_list(self):
        """폴더 목록 새로고침"""
        self.folder_list.clear()
        for folder in self.shared_folders:
            self.folder_list.addItem(folder)
    
    def add_user_dialog(self):
        """사용자 추가 대화상자"""
        dialog = AddUserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            username = dialog.username_entry.text().strip()
            password = dialog.password_entry.text().strip()
            
            if not username or not password:
                QMessageBox.critical(self, "오류", "아이디와 비밀번호를 입력하세요.")
                return
            
            if username in self.users:
                QMessageBox.critical(self, "오류", "이미 존재하는 아이디입니다.")
                return
            
            self.users[username] = password
            self.save_config()
            self.refresh_user_list()
    
    def remove_user(self):
        """사용자 제거"""
        current_item = self.user_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "제거할 사용자를 선택하세요.")
            return
        
        username = current_item.text()
        reply = QMessageBox.question(self, "확인", 
                                     f"사용자 '{username}'을(를) 제거하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            del self.users[username]
            self.save_config()
            self.refresh_user_list()
    
    def add_folder(self):
        """공유 폴더 추가"""
        folder = QFileDialog.getExistingDirectory(self, "공유할 폴더 선택")
        if folder:
            if folder not in self.shared_folders:
                self.shared_folders.append(folder)
                self.save_config()
                self.refresh_folder_list()
            else:
                QMessageBox.information(self, "정보", "이미 추가된 폴더입니다.")
    
    def remove_folder(self):
        """공유 폴더 제거"""
        current_item = self.folder_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "경고", "제거할 폴더를 선택하세요.")
            return
        
        folder = current_item.text()
        reply = QMessageBox.question(self, "확인",
                                     f"폴더를 제거하시겠습니까?\n{folder}",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.shared_folders.remove(folder)
            self.save_config()
            self.refresh_folder_list()
    
    def start_unified_server(self):
        """통합 서버 시작"""
        if not self.users:
            QMessageBox.critical(self, "오류", "최소 1명의 사용자를 추가하세요.")
            return
        
        if not self.shared_folders:
            QMessageBox.critical(self, "오류", "최소 1개의 공유 폴더를 추가하세요.")
            return
        
        # 버튼 비활성화
        self.start_btn.setEnabled(False)
        self.start_btn.setText("시작 중...")
        self.status_label.setText("서버 시작 중...")
        self.status_label.setStyleSheet("color: orange;")
        
        # 서버 시작 스레드
        self.server_thread = ServerThread(self.users, self.shared_folders, self.tunnel_manager)
        self.server_thread.status_update.connect(self.on_status_update)
        self.server_thread.tunnel_created.connect(self.on_tunnel_created)
        self.server_thread.error_occurred.connect(self.on_error)
        self.server_thread.start()
    
    def on_status_update(self, message, color):
        """상태 업데이트"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
    
    def on_tunnel_created(self, url):
        """터널 생성 완료"""
        self.tunnel_url = url
        self.server_running = True
        self.show_running_screen()
    
    def on_error(self, error_msg):
        """에러 발생"""
        QMessageBox.critical(self, "오류", error_msg)
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 서버 시작 (원거리 접속 자동)")
        self.status_label.setText("준비됨")
        self.status_label.setStyleSheet("color: #2563eb;")
    
    def show_running_screen(self):
        """서버 실행 중 화면"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 제목
        title = QLabel("✅ 서버 실행 중")
        title.setFont(QFont("맑은 고딕", 22, QFont.Bold))
        title.setStyleSheet("color: #10b981;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 접속 정보
        info_group = QGroupBox("🔑 클라이언트에게 전달할 정보")
        info_layout = QVBoxLayout(info_group)
        
        key_label = QLabel("접속키:")
        key_label.setFont(QFont("맑은 고딕", 13, QFont.Bold))
        info_layout.addWidget(key_label)
        
        self.key_text = QTextEdit()
        self.key_text.setMaximumHeight(80)
        self.key_text.setText(self.tunnel_url)
        self.key_text.setReadOnly(True)
        self.key_text.setStyleSheet("background-color: #1a4d2e; color: #ffffff;")
        info_layout.addWidget(self.key_text)
        
        copy_btn = QPushButton("📋 클립보드에 복사")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        info_layout.addWidget(copy_btn)
        
        # 사용 안내
        usage_text = f"""
📱 클라이언트 사용법:

1. client_run.exe 실행
2. 위의 접속키를 복사해서 붙여넣기
3. 등록된 아이디/비밀번호로 로그인
4. 공유 폴더에 접근!

등록된 사용자: {', '.join(self.users.keys())}
공유 폴더 수: {len(self.shared_folders)}개
"""
        
        usage_label = QLabel(usage_text)
        usage_label.setWordWrap(True)
        info_layout.addWidget(usage_label)
        
        layout.addWidget(info_group)
        
        # 버튼
        btn_layout = QHBoxLayout()
        
        restart_btn = QPushButton("🔄 새 키 생성 (서버 재시작)")
        restart_btn.clicked.connect(self.restart_server)
        btn_layout.addWidget(restart_btn)
        
        stop_btn = QPushButton("🛑 서버 중지")
        stop_btn.setObjectName("stopBtn")
        stop_btn.clicked.connect(self.stop_server)
        btn_layout.addWidget(stop_btn)
        
        minimize_btn = QPushButton("⬇️ 최소화 (백그라운드)")
        minimize_btn.clicked.connect(self.minimize_to_tray)
        btn_layout.addWidget(minimize_btn)
        
        layout.addLayout(btn_layout)
        
        tip = QLabel("💡 최소화하면 시스템 트레이에서 실행됩니다")
        tip.setStyleSheet("color: #999999;")
        tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(tip)
    
    def copy_to_clipboard(self):
        """클립보드에 복사"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.tunnel_url)
        QMessageBox.information(self, "복사 완료", "접속키가 클립보드에 복사되었습니다!")
    
    def restart_server(self):
        """서버 재시작"""
        reply = QMessageBox.question(self, "확인",
                                     "서버를 재시작하시겠습니까?\n새로운 접속 키가 생성됩니다.",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.stop_server()
            self.create_setup_screen()
    
    def stop_server(self):
        """서버 중지"""
        reply = QMessageBox.question(self, "확인", "서버를 중지하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.tunnel_manager.stop_tunnel()
            self.server_running = False
            self.create_setup_screen()
    
    def minimize_to_tray(self):
        """시스템 트레이로 최소화"""
        self.hide()
        self.create_tray_icon()
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.server_running:
            reply = QMessageBox.question(self, "최소화",
                                        "서버가 실행 중입니다.\n백그라운드로 최소화하시겠습니까?",
                                        QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                event.ignore()
                self.minimize_to_tray()
            else:
                event.accept()
        else:
            event.accept()
    
    def create_tray_icon(self):
        """시스템 트레이 아이콘 생성"""
        # 간단한 아이콘 생성
        image = Image.new('RGB', (64, 64), color='#10b981')
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 10, 54, 54], fill='white')
        draw.text((20, 20), "FS", fill='#10b981')
        
        menu = pystray.Menu(
            pystray.MenuItem("서버 실행 중" if self.server_running else "서버 대기 중", 
                            lambda: None, enabled=False),
            pystray.MenuItem("열기", self.show_window),
            pystray.MenuItem("서버 중지" if self.server_running else "종료", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("file_share_server", image, "파일 공유 서버", menu)
        
        # 트레이 아이콘을 별도 스레드에서 실행
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def show_window(self):
        """창 다시 표시"""
        self.show()
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
    
    def quit_app(self):
        """앱 종료"""
        if self.server_running:
            self.tunnel_manager.stop_tunnel()
        if self.tray_icon:
            self.tray_icon.stop()
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    
    window = UnifiedFileShareServer()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
