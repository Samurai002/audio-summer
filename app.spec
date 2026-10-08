# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Собираем ресурсы CustomTkinter (цветовые темы и шрифты)
datas = collect_data_files('customtkinter')

# Добавляем ffmpeg.exe в корень сборки (если он присутствует при компиляции)
import os
if os.path.exists('ffmpeg.exe'):
    datas.append(('ffmpeg.exe', '.'))

# Собираем скрытые импорты для faster_whisper и ctranslate2
hiddenimports = [
    'customtkinter',
    'faster_whisper',
    'ctranslate2',
    'requests',
    'pydub',
] + collect_submodules('faster_whisper')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='AudioSummarizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # False = оконный режим (без черного окна консоли)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)