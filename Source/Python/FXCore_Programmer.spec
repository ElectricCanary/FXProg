# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

binaries = [
   ('C:\\Windows\\System32\\libusb0.dll', '.'),
]


a = Analysis(
    ['C:\\\\Users\\\\antoi\\\\Desktop\\\\EC\\\\FXCore_Programmer\\\\FXCore_Programmer\\\\FXCore_Programmer\\\\FXCore_Programmer.py'],
    pathex=[],
    binaries=binaries,
    datas=[],
    hiddenimports=['usb'],
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
    [],
    exclude_binaries=True,
    name='FXCore_Programmer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FXCore_Programmer',
)
