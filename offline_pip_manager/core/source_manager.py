"""Source management: CRUD for pip mirror sources with connection testing."""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


DEFAULT_SOURCES = [
    {"name": "清华", "url": "https://pypi.tuna.tsinghua.edu.cn/simple", "enabled": True},
    {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple", "enabled": True},
    {"name": "中科大", "url": "https://pypi.mirrors.ustc.edu.cn/simple", "enabled": True},
    {"name": "豆瓣", "url": "https://pypi.douban.com/simple", "enabled": False},
    {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple", "enabled": False},
    {"name": "PyPI官方", "url": "https://pypi.org/simple", "enabled": True},
]


class SourceManager:
    """Manage pip mirror sources with persistence to a JSON config file."""

    def __init__(self, config_path: str):
        self._config_path = Path(config_path)
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Create default config file if it doesn't exist."""
        if not self._config_path.exists():
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"sources": DEFAULT_SOURCES.copy()}
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_config(self) -> dict:
        """Read the full config file."""
        with open(self._config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_config(self, data: dict):
        """Write the full config file."""
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> list[dict]:
        """Load the source list from config."""
        config = self._read_config()
        return config.get("sources", [])

    def save(self, sources: list[dict]):
        """Save the source list to config."""
        config = self._read_config()
        config["sources"] = sources
        self._write_config(config)

    def get_enabled(self) -> list[dict]:
        """Return only enabled sources, in priority order."""
        return [s for s in self.load() if s.get("enabled", False)]

    def add(self, name: str, url: str):
        """Add a new source (enabled by default)."""
        sources = self.load()
        sources.append({"name": name, "url": url, "enabled": True})
        self.save(sources)

    def remove(self, index: int):
        """Remove a source by index."""
        sources = self.load()
        if 0 <= index < len(sources):
            sources.pop(index)
            self.save(sources)

    def move_up(self, index: int):
        """Move a source up in priority (smaller index = higher priority)."""
        if index <= 0 or index >= len(self.load()):
            return
        sources = self.load()
        sources[index], sources[index - 1] = sources[index - 1], sources[index]
        self.save(sources)

    def move_down(self, index: int):
        """Move a source down in priority."""
        sources = self.load()
        if index < 0 or index >= len(sources) - 1:
            return
        sources[index], sources[index + 1] = sources[index + 1], sources[index]
        self.save(sources)

    def toggle(self, index: int):
        """Toggle the enabled status of a source."""
        sources = self.load()
        if 0 <= index < len(sources):
            sources[index]["enabled"] = not sources[index].get("enabled", True)
            self.save(sources)

    def test_connection(self, url: str, timeout: int = 10) -> tuple[bool, str]:
        """Test if a source URL is reachable.

        Returns:
            (is_ok, message)
        """
        try:
            req = urllib.request.Request(url, method="HEAD")
            req.add_header("User-Agent", "OfflinePipManager/1.0")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    return True, "连接成功"
                return False, f"HTTP {response.status}"
        except urllib.error.HTTPError as e:
            return False, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return False, f"网络错误: {e.reason}"
        except Exception as e:
            return False, f"未知错误: {e}"
