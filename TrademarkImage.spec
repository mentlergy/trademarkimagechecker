# PyInstaller build specification. Build with:  pyinstaller --noconfirm --clean TrademarkImage.spec
from PyInstaller.utils.hooks import collect_all

# tkinterdnd2 ships the native tkdnd library as package data; it must be bundled.
dnd_datas, dnd_binaries, dnd_hidden = collect_all("tkinterdnd2")


def windows_only(entries):
    """Drop the Linux and macOS builds of tkdnd that tkinterdnd2 also ships."""
    return [e for e in entries if "tkdnd" not in e[1] or "\\win-" in e[1] or "/win-" in e[1]]


dnd_datas, dnd_binaries = windows_only(dnd_datas), windows_only(dnd_binaries)

a = Analysis(
    ["run_trademarkimage.py"],
    pathex=[],
    binaries=dnd_binaries,
    datas=dnd_datas,
    hiddenimports=dnd_hidden + ["PIL._tkinter_finder"],
    excludes=["pytest", "docx", "lxml", "numpy"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="TrademarkImage",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # GUI application: no console window
    version=None,
)
