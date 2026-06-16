"""Tests for core.checker."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "offline_pip_manager"))

from core.checker import VersionChecker
from core.source_manager import SourceManager


@pytest.fixture
def source_manager():
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({
            "sources": [
                {"name": "PyPI", "url": "https://pypi.org/simple", "enabled": True},
            ]
        }, f)
        path = f.name
    sm = SourceManager(path)
    yield sm
    Path(path).unlink(missing_ok=True)


def _mock_response(data: dict):
    """Create a mock HTTP response with JSON data."""
    mock = MagicMock()
    mock.status = 200
    mock.read.return_value = json.dumps(data).encode("utf-8")
    mock.__enter__.return_value = mock
    return mock


class TestVersionChecker:

    @patch("urllib.request.urlopen")
    def test_has_update(self, mock_urlopen, source_manager):
        """Local version is older than PyPI."""
        mock_urlopen.return_value = _mock_response({
            "info": {"version": "2.0.0"}
        })

        checker = VersionChecker(source_manager)
        result = checker.check_package("requests", "1.0.0")

        assert result is not None
        assert result["name"] == "requests"
        assert result["local"] == "1.0.0"
        assert result["latest"] == "2.0.0"
        assert result["has_update"] is True

    @patch("urllib.request.urlopen")
    def test_no_update(self, mock_urlopen, source_manager):
        """Local version is current."""
        mock_urlopen.return_value = _mock_response({
            "info": {"version": "1.0.0"}
        })

        checker = VersionChecker(source_manager)
        result = checker.check_package("requests", "1.0.0")

        assert result is not None
        assert result["has_update"] is False

    @patch("urllib.request.urlopen")
    def test_local_newer(self, mock_urlopen, source_manager):
        """Local version is actually newer (e.g., pre-release)."""
        mock_urlopen.return_value = _mock_response({
            "info": {"version": "1.0.0"}
        })

        checker = VersionChecker(source_manager)
        result = checker.check_package("requests", "2.0.0b1")

        assert result is not None
        assert result["has_update"] is False  # local is pre-release but newer

    @patch("urllib.request.urlopen")
    def test_network_error(self, mock_urlopen, source_manager):
        """Network error returns None."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("timeout")

        checker = VersionChecker(source_manager)
        result = checker.check_package("requests", "1.0.0")

        assert result is None

    @patch("urllib.request.urlopen")
    def test_check_all(self, mock_urlopen, source_manager):
        """Check multiple packages at once."""
        # Return different versions for different packages
        def urlopen_side_effect(req, *args, **kwargs):
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            if "openpyxl" in url:
                return _mock_response({"info": {"version": "3.2.0"}})
            elif "numpy" in url:
                return _mock_response({"info": {"version": "1.26.0"}})
            return _mock_response({"info": {"version": "0.0.0"}})

        mock_urlopen.side_effect = urlopen_side_effect

        checker = VersionChecker(source_manager)
        packages = [
            {"name": "openpyxl", "version": "3.1.5"},
            {"name": "numpy", "version": "1.26.0"},
            {"name": "unknown", "version": "0.1.0"},
        ]
        results = checker.check_all(packages)

        assert len(results) == 3
        assert results[0]["has_update"] is True   # openpyxl: 3.1.5 < 3.2.0
        assert results[1]["has_update"] is False  # numpy: same version
        assert results[2]["has_update"] is False  # unknown: "latest" = 0.0.0 < 0.1.0
