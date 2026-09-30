# Build on the target OS: python -m PyInstaller --clean main.spec
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(['main.py'], pathex=[], binaries=[],
             datas=collect_data_files('kivymd'),
             hiddenimports=collect_submodules('kivymd') + ['medmate.screens'],
             hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Medmate',
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Medmate')
