# -*- mode: python ; coding: utf-8 -*-
# macOS용 서버 빌드 스펙 파일

import os
from pathlib import Path

block_cipher = None

# templates 폴더 경로 (상위 폴더에 있을 수 있음)
templates_path = '../templates'
if not os.path.exists(templates_path):
    templates_path = 'templates'

datas_list = []
if os.path.exists(templates_path):
    datas_list.append((templates_path, 'templates'))

a = Analysis(
    ['unified_server_pyqt.py'],
    pathex=[],
    binaries=[],
    datas=datas_list,
    hiddenimports=[
        'flask',
        'werkzeug',
        'werkzeug.security',
        'waitress',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'pystray',
        'cloudflared_manager',
        'server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Woori_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 앱이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS용 .app 번들 생성
app = BUNDLE(
    exe,
    name='Woori_Server.app',
    icon=None,  # 아이콘 파일이 있다면 경로 지정
    bundle_identifier='com.woori.fileshare.server',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Woori Server',
        'CFBundleDisplayName': 'Woori 파일 공유 서버',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSRequiresAquaSystemAppearance': 'False',  # 다크 모드 지원
    },
)
