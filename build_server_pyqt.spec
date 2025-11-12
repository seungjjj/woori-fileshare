# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# templates 폴더를 포함
datas = []
if os.path.exists('templates'):
    datas.append(('templates', 'templates'))

a = Analysis(
    ['unified_server_pyqt.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask', 'werkzeug', 'jinja2', 'click', 'itsdangerous', 'markupsafe',
        'waitress', 'PIL', 'pystray', 'requests', 'urllib3', 'charset_normalizer',
        'certifi', 'idna', 'cloudflared_manager', 'server'
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
    name='Woori_Server_PyQt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 서버이므로 콘솔 숨김 (시스템 트레이로 제어)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='server_icon.ico' if os.path.exists('server_icon.ico') else None,
)
