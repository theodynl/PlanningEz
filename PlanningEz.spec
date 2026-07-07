# PyInstaller spec for the PlanningEz standalone executable.
#
# Bundles the FastAPI server, the PlanningEz core and the built frontend
# (frontend/dist) into a single onefile executable. Build with:
#
#     pyinstaller PlanningEz.spec
#
# The frontend must be built first (``cd frontend && npm run build``) so that
# frontend/dist exists.

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("frontend/dist", "frontend/dist")]
binaries = []
hiddenimports = []

# uvicorn/fastapi pull in a number of modules dynamically; collect them fully.
for pkg in ("uvicorn", "fastapi", "starlette", "anyio", "click", "h11"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Ensure the whole application package is included even where imports are
# resolved lazily.
hiddenimports += collect_submodules("planningez")


block_cipher = None

a = Analysis(
    ["planningez/launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter"],
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
    name="PlanningEz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
