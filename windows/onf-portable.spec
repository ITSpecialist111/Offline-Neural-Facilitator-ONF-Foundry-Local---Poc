from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

root = Path(SPECPATH).parent

binaries = []
datas = [
    (str(root / "frontend" / "dist"), "frontend_dist"),
    (str(root / "knowledge"), "knowledge"),
    (str(root / "skills"), "skills"),
    (str(root / "LICENSE"), "."),
]
hiddenimports = []

for package in (
    "chromadb",
    "ctranslate2",
    "faster_whisper",
    "huggingface_hub",
    "openai",
    "PIL",
    "pystray",
    "reportlab",
    "tokenizers",
    "uvicorn",
    "websockets",
):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

hiddenimports += collect_submodules("python_multipart")
hiddenimports = sorted(set(hiddenimports))

analysis = Analysis(
    [str(root / "desktop_launcher.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "melo",
        "tensorflow",
        "torch",
        "torchaudio",
        "transformers",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="ONF",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "windows" / "onf.ico"),
    version=str(root / "windows" / "version_info.txt"),
)

bundle = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ONF-Windows-Portable",
)
