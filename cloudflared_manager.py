"""
Cloudflared 터널 자동 관리 모듈
서버 실행 시 자동으로 터널을 생성하고 URL을 반환
"""
import os
import sys
import subprocess
import requests
import zipfile
import platform
import time
import json
from pathlib import Path
import threading

class CloudflaredManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.cloudflared_dir = os.path.join(self.base_dir, 'cloudflared')
        os.makedirs(self.cloudflared_dir, exist_ok=True)
        
        # OS별 실행 파일명
        if platform.system() == 'Windows':
            self.cloudflared_exe = os.path.join(self.cloudflared_dir, 'cloudflared.exe')
        else:
            self.cloudflared_exe = os.path.join(self.cloudflared_dir, 'cloudflared')
        
        self.process = None
        self.tunnel_url = None
        self.status_callback = None
    
    def is_installed(self):
        """cloudflared가 설치되어 있는지 확인"""
        return os.path.exists(self.cloudflared_exe)
    
    def download_cloudflared(self, progress_callback=None):
        """cloudflared 자동 다운로드"""
        try:
            if progress_callback:
                progress_callback("Cloudflared 다운로드 중...")
            
            # Windows 64bit 기준
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.cloudflared_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(f"다운로드 중... {percent:.1f}%")
            
            if progress_callback:
                progress_callback("다운로드 완료!")
            
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"다운로드 실패: {e}")
            return False
    
    def ensure_installed(self, progress_callback=None):
        """설치 확인 및 필요시 다운로드"""
        if not self.is_installed():
            return self.download_cloudflared(progress_callback)
        return True
    
    def start_tunnel(self, local_port=5000, status_callback=None):
        """터널 시작 및 URL 반환"""
        self.status_callback = status_callback
        
        if not self.ensure_installed(status_callback):
            return None
        
        try:
            if status_callback:
                status_callback("터널 시작 중...")
            
            # cloudflared tunnel 실행
            cmd = [self.cloudflared_exe, 'tunnel', '--url', f'http://localhost:{local_port}']
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == 'Windows' else 0
            )
            
            # URL 추출을 위한 스레드
            def read_output():
                for line in iter(self.process.stdout.readline, ''):
                    if not line:
                        break
                    
                    # trycloudflare.com URL 찾기
                    if 'trycloudflare.com' in line or 'https://' in line:
                        # URL 추출
                        parts = line.split()
                        for part in parts:
                            if 'trycloudflare.com' in part:
                                # https:// 부터 추출
                                if 'https://' in part:
                                    url = part[part.find('https://'):]
                                    # 불필요한 문자 제거
                                    url = url.split()[0].rstrip('.,;')
                                    self.tunnel_url = url
                                    if self.status_callback:
                                        self.status_callback(f"터널 생성 완료: {url}")
                                    break
            
            thread = threading.Thread(target=read_output, daemon=True)
            thread.start()
            
            # URL이 생성될 때까지 대기 (최대 30초)
            for _ in range(60):
                if self.tunnel_url:
                    return self.tunnel_url
                time.sleep(0.5)
            
            if status_callback:
                status_callback("터널 URL을 가져오는 데 시간이 걸립니다...")
            
            return None
            
        except Exception as e:
            if status_callback:
                status_callback(f"터널 시작 실패: {e}")
            return None
    
    def stop_tunnel(self):
        """터널 중지"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                try:
                    self.process.kill()
                except:
                    pass
            self.process = None
            self.tunnel_url = None
    
    def get_tunnel_url(self):
        """현재 터널 URL 반환"""
        return self.tunnel_url
    
    def is_running(self):
        """터널이 실행 중인지 확인"""
        if self.process:
            return self.process.poll() is None
        return False


if __name__ == "__main__":
    # 테스트
    manager = CloudflaredManager()
    
    def callback(msg):
        print(f"[STATUS] {msg}")
    
    print("터널 시작...")
    url = manager.start_tunnel(5000, callback)
    
    if url:
        print(f"\n✅ 터널 URL: {url}")
        input("엔터를 누르면 종료합니다...")
    else:
        print("\n❌ 터널 생성 실패")
    
    manager.stop_tunnel()
