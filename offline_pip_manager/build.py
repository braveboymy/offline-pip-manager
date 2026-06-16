"""Build script for PyInstaller single-exe packaging.

Usage:
    python build.py            # build exe
    python build.py --clean    # clean build
"""

import subprocess
import sys
import shutil
from pathlib import Path


def build(clean: bool = False):
    """Package the app into a single .exe using PyInstaller."""
    root = Path(__file__).parent

    # Clean previous builds
    if clean:
        for d in ["build", "dist"]:
            shutil.rmtree(root / d, ignore_errors=True)
        for spec in root.glob("*.spec"):
            spec.unlink()

    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",           # no console window
        "--name", "离线pip包管理器",
        "--add-data", f"{root / 'config.json'}{';' if sys.platform == 'win32' else ':'}.",
        "--hidden-import", "customtkinter",
        "--hidden-import", "packaging",
        str(root / "main.py"),
    ]

    print(f"Building with command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(root))
    
    if result.returncode == 0:
        exe_path = root / "dist" / "离线pip包管理器.exe"
        print(f"\n✓ Build successful!")
        print(f"  Output: {exe_path}")
        print(f"  Size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    clean = "--clean" in sys.argv
    build(clean=clean)
