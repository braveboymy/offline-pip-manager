"""Offline installer — installs packages from a local wheel directory."""

import subprocess
import sys
from typing import Callable, Optional


class Installer:
    """Install Python packages from a local directory (offline)."""

    def __init__(self, store_dir: str, python_path: str = "python"):
        self._store_dir = store_dir
        self._python_path = python_path

    def install(
        self,
        packages: list[str],
        on_log: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Install packages from the local store directory.

        Args:
            packages: List of package names to install.
            on_log: Called with each output line.

        Returns:
            True if installation succeeded.
        """
        if not packages:
            self._emit_log(on_log, "没有选择要安装的包。")
            return False

        cmd = [
            self._python_path, "-m", "pip", "install",
            "--no-index",
            "--find-links", self._store_dir,
        ] + packages

        self._emit_log(on_log, f"命令: {' '.join(cmd)}")
        self._emit_log(on_log, f"安装 {len(packages)} 个包到 {self._store_dir}...")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            for line in iter(process.stdout.readline, ""):
                line = line.rstrip("\n\r")
                self._emit_log(on_log, line)

            process.wait()

            if process.returncode == 0:
                self._emit_log(on_log, "✓ 安装成功！")
                return True
            else:
                self._emit_log(on_log, f"✗ 安装失败 (exit code: {process.returncode})")
                return False

        except FileNotFoundError:
            self._emit_log(on_log, f"✗ 找不到 Python 解释器: {self._python_path}")
            return False
        except Exception as e:
            self._emit_log(on_log, f"✗ 安装出错: {e}")
            return False

    def _emit_log(self, callback: Optional[Callable], line: str):
        if callback:
            callback(line)
