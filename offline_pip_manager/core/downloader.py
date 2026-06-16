"""Pip downloader with automatic source failover."""

import subprocess
import sys
import threading
from typing import Callable, Optional


class Downloader:
    """Download Python packages with automatic mirror source failover."""

    def __init__(
        self,
        source_manager: any,
        store_dir: str,
        timeout: int = 30,
    ):
        self._source_manager = source_manager
        self._store_dir = store_dir
        self._timeout = timeout

    def download(
        self,
        package: str,
        version: Optional[str] = None,
        with_deps: bool = True,
        on_progress: Optional[Callable[[int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """Download a package and optionally its dependencies.

        Tries enabled sources in priority order. Fails over automatically.

        Args:
            package: Package name.
            version: Specific version or None for latest.
            with_deps: Whether to download dependencies.
            on_progress: Called with progress percentage (0-100).
            on_log: Called with each output line.

        Returns:
            True if download succeeded, False if all sources failed.
        """
        pkg_spec = package if version is None else f"{package}=={version}"
        enabled_sources = self._source_manager.get_enabled()

        if not enabled_sources:
            self._emit_log(on_log, "错误: 没有可用的镜像源。请在「源管理」中启用至少一个源。")
            return False

        for idx, source in enumerate(enabled_sources):
            source_url = source["url"]
            source_name = source["name"]

            self._emit_log(on_log, f"[{idx + 1}/{len(enabled_sources)}] 尝试源: {source_name} ({source_url})")
            self._emit_progress(on_progress, 5)

            cmd = [
                sys.executable, "-m", "pip", "download",
                pkg_spec,
                "-d", self._store_dir,
                "-i", source_url,
            ]
            if not with_deps:
                cmd.append("--no-deps")

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

                output_lines = []
                for line in iter(process.stdout.readline, ""):
                    line = line.rstrip("\n\r")
                    output_lines.append(line)
                    self._emit_log(on_log, line)

                    # Rough progress estimation based on pip output
                    if "Downloading" in line:
                        self._emit_progress(on_progress, 40)
                    elif "Saved" in line or "Successfully" in line:
                        self._emit_progress(on_progress, 90)

                process.wait(timeout=self._timeout)

                if process.returncode == 0:
                    self._emit_log(on_log, f"✓ 下载成功 (源: {source_name})")
                    self._emit_progress(on_progress, 100)
                    return True
                else:
                    self._emit_log(on_log, f"✗ 源 {source_name} 下载失败 (exit code: {process.returncode})")
                    self._emit_log(on_log, f"  尝试下一个源...")
                    self._emit_progress(on_progress, 10)

            except subprocess.TimeoutExpired:
                process.kill()
                self._emit_log(on_log, f"✗ 源 {source_name} 超时 ({self._timeout}s)")
            except Exception as e:
                self._emit_log(on_log, f"✗ 源 {source_name} 错误: {e}")

        self._emit_log(on_log, "✗ 所有镜像源均下载失败。请检查网络连接或源配置。")
        self._emit_progress(on_progress, 0)
        return False

    def _emit_log(self, callback: Optional[Callable], line: str):
        if callback:
            callback(line)

    def _emit_progress(self, callback: Optional[Callable], value: int):
        if callback:
            callback(value)
