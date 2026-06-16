"""Offline Pip Manager — Entry Point.

A desktop GUI tool for downloading Python packages with dependencies
and installing them offline on air-gapped Windows machines.
"""

import sys
import subprocess


def get_python() -> str:
    """Return the correct Python executable to use for pip subprocess.

    When packaged by PyInstaller (sys.frozen=True), sys.executable points to
    the packaged .exe itself. Using it to run pip would re-launch the GUI app
    in an infinite loop. We must use the system Python instead.
    """
    if getattr(sys, "frozen", False):
        return "python"  # use system PATH
    return sys.executable  # dev mode: use current interpreter


def check_pip():
    """Verify pip is available."""
    try:
        subprocess.run(
            [get_python(), "-m", "pip", "--version"],
            capture_output=True, check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


if __name__ == "__main__":
    if not check_pip():
        import tkinter.messagebox as mb
        mb.showerror(
            "错误",
            "未找到 pip。请确保 Python 已正确安装并添加到 PATH。\n\n"
            "如果已安装 Python，请尝试在终端运行: python -m ensurepip"
        )
        sys.exit(1)

    from app import App
    app = App()
    app.mainloop()
