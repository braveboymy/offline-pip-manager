"""Version checker — compares local packages against PyPI JSON API."""

import json
import urllib.request
import urllib.error
from typing import Optional

from packaging.version import parse as parse_version


class VersionChecker:
    """Check if local packages have newer versions on PyPI."""

    def __init__(self, source_manager: any, timeout: int = 15):
        self._source_manager = source_manager
        self._timeout = timeout

    def check_package(self, name: str, local_version: str) -> Optional[dict]:
        """Check a single package for updates.

        Args:
            name: Package name (canonical).
            local_version: Version string of the local package.

        Returns:
            dict with name, local, latest, has_update — or None on error.
        """
        # Try enabled sources for the JSON API
        # PyPI JSON API is at https://pypi.org/pypi/{name}/json
        # For mirrors, we use the canonical PyPI JSON API directly
        for source in self._source_manager.get_enabled():
            source_url = source["url"]
            # Build JSON API URL from the simple index URL
            if "pypi.org" in source_url:
                api_url = f"https://pypi.org/pypi/{name}/json"
            else:
                # For mirrors, also try the PyPI JSON API directly
                # as mirrors may not have the JSON API
                api_url = f"https://pypi.org/pypi/{name}/json"

            try:
                req = urllib.request.Request(api_url)
                req.add_header("User-Agent", "OfflinePipManager/1.0")
                req.add_header("Accept", "application/json")

                with urllib.request.urlopen(req, timeout=self._timeout) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        latest_version = data.get("info", {}).get("version", "0.0.0")
                        break
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError):
                continue
        else:
            # All sources failed
            return None

        try:
            local_parsed = parse_version(local_version)
            latest_parsed = parse_version(latest_version)
            has_update = latest_parsed > local_parsed
        except Exception:
            has_update = False

        return {
            "name": name,
            "local": local_version,
            "latest": latest_version,
            "has_update": has_update,
        }

    def check_all(self, packages: list[dict]) -> list[dict]:
        """Check multiple packages for updates.

        Args:
            packages: List of dicts with 'name' and 'version' keys.

        Returns:
            List of result dicts (same order as input). Packages that couldn't
            be checked have has_update=False and latest="(检查失败)".
        """
        results = []
        for pkg in packages:
            result = self.check_package(pkg["name"], pkg["version"])
            if result is None:
                result = {
                    "name": pkg["name"],
                    "local": pkg["version"],
                    "latest": "(检查失败)",
                    "has_update": False,
                }
            results.append(result)
        return results
