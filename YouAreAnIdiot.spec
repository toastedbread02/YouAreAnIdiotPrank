from PyInstaller.utils.hooks import collect_submodules

VLC_DIR = r"C:\Program Files\VideoLAN\VLC"

a = Analysis(
    ["youareanidiot.py"],
    pathex=[],
    binaries=[
        (VLC_DIR + r"\libvlc.dll", "."),
        (VLC_DIR + r"\libvlccore.dll", "."),
    ],
    datas=[
        (VLC_DIR + r"\plugins", "plugins"),
        ("youareanidiot!.mp4", "."),
        ("youareanidiot!.mp3", "."),
        ("youareanidiot1.png", "."),
        ("youareanidiot2.png", "."),
    ],
    hiddenimports=collect_submodules("vlc"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="YouAreAnIdiot",
    debug=False,
    strip=False,
    upx=True,
    console=False,
)
