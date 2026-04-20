# PyInstaller spec for building a standalone `quell` binary.
#
# Usage:
#   pip install pyinstaller
#   pyinstaller packaging/pyinstaller/quell.spec --clean --noconfirm
#
# Output: ./dist/quell/quell  (plus a directory of shared libs alongside).
#
# The "onefile" variant produces a single executable but extracts to a
# temp dir at startup — we prefer onedir for fast startup, which
# matters for the `quell doctor` / `quell --help` dev-loop UX.
#
# CI packs the resulting directory into a .tar.gz / .zip before
# attaching to the GitHub release.

# ruff: noqa  (PyInstaller specs are Python but evaluated oddly)

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ---------------------------------------------------------------------------
# Data files — ship bundled skills + the Jinja system prompt template.
# ---------------------------------------------------------------------------

datas = []

# The bundled markdown skills under quell/skills/<category>/*.md
datas += collect_data_files("quell.skills", includes=["**/*.md"])

# Jinja templates living beside Python modules.
datas += collect_data_files(
    "quell.agents.incident_commander", includes=["*.jinja"]
)

# ---------------------------------------------------------------------------
# Hidden imports — PyInstaller's static analyser misses several runtime
# imports (tool modules, LiteLLM provider plugins, SQLAlchemy dialects).
# ---------------------------------------------------------------------------

hiddenimports: list[str] = []
hiddenimports += collect_submodules("quell")
hiddenimports += collect_submodules("litellm")
hiddenimports += [
    "aiosqlite",
    "sqlalchemy.dialects.sqlite",
    "jinja2.ext",
    "yaml",
]

a = Analysis(
    ["../../quell/__main__.py"],
    pathex=["../.."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tests", "pytest"],
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
    name="quell",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="quell",
)
