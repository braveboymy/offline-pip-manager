"""Local package directory scanner — finds wheel and source distributions."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from packaging.utils import parse_wheel_filename, canonicalize_name


def scan_directory(directory: str) -> list[dict]:
    """Scan a directory for .whl and .tar.gz/.zip source files.

    Args:
        directory: Path to the directory to scan.

    Returns:
        List of dicts with keys: name, version, filename, path, size, date.
        Sorted by name.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")

    packages: list[dict] = []

    for entry in sorted(dir_path.iterdir()):
        if not entry.is_file():
            continue

        pkg_info = _parse_filename(entry)
        if pkg_info is None:
            continue

        stat = entry.stat()
        pkg_info["filename"] = entry.name
        pkg_info["path"] = str(entry)
        pkg_info["size"] = stat.st_size
        pkg_info["date"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        packages.append(pkg_info)

    packages.sort(key=lambda p: p["name"])
    return packages


def _parse_filename(filepath: Path) -> Optional[dict]:
    """Parse a package filename to extract name and version.

    Supports .whl and .tar.gz/.zip formats.
    """
    name_lower = filepath.name.lower()

    if name_lower.endswith(".whl"):
        return _parse_wheel(filepath.name)
    elif name_lower.endswith(".tar.gz"):
        return _parse_sdist(filepath.name, suffix=".tar.gz")
    elif name_lower.endswith(".zip") and ".whl" not in name_lower:
        return _parse_sdist(filepath.name, suffix=".zip")

    return None


def _parse_wheel(filename: str) -> Optional[dict]:
    """Parse a wheel filename using packaging.utils.parse_wheel_filename."""
    try:
        name, version, *_ = parse_wheel_filename(filename)
        return {
            "name": canonicalize_name(name),
            "version": str(version),
        }
    except Exception:
        return None


def _parse_sdist(filename: str, suffix: str) -> Optional[dict]:
    """Parse a source distribution filename like name-version.tar.gz.

    Falls back to regex since packaging doesn't have a direct sdist parser.
    """
    import re

    basename = filename[: -len(suffix)]
    # Match: name-version (name can contain hyphens, version is at the end)
    # e.g., "requests-2.31.0" → name="requests", version="2.31.0"
    match = re.match(r"^(.+)-(\d[^-]*?)$", basename)
    if match:
        return {
            "name": canonicalize_name(match.group(1)),
            "version": match.group(2),
        }
    return None
