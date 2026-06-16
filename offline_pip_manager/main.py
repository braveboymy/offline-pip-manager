"""Offline Pip Manager — Entry Point.

A desktop GUI tool for downloading Python packages with dependencies
and installing them offline on air-gapped Windows machines.
"""

import sys
import subprocess


def check_pip():
    """Verify pip is available."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, check=True,
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
