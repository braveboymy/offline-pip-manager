"""Tests for core.source_manager."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "offline_pip_manager"))

from core.source_manager import SourceManager


@pytest.fixture
def temp_config():
    """Create a temporary config file with test data."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({
            "sources": [
                {"name": "SourceA", "url": "https://a.example.com/simple", "enabled": True},
                {"name": "SourceB", "url": "https://b.example.com/simple", "enabled": False},
                {"name": "SourceC", "url": "https://c.example.com/simple", "enabled": True},
            ]
        }, f)
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


@pytest.fixture
def empty_config():
    """Create a config file with no sources."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"sources": []}, f)
        path = f.name
    yield path
    Path(path).unlink(missing_ok=True)


class TestSourceManager:
    """Tests for SourceManager CRUD operations."""

    def test_load_sources(self, temp_config):
        sm = SourceManager(temp_config)
        sources = sm.load()
        assert len(sources) == 3
        assert sources[0]["name"] == "SourceA"

    def test_get_enabled(self, temp_config):
        sm = SourceManager(temp_config)
        enabled = sm.get_enabled()
        assert len(enabled) == 2
        assert enabled[0]["name"] == "SourceA"
        assert enabled[1]["name"] == "SourceC"

    def test_get_enabled_empty(self, empty_config):
        sm = SourceManager(empty_config)
        enabled = sm.get_enabled()
        assert len(enabled) == 0

    def test_add_source(self, temp_config):
        sm = SourceManager(temp_config)
        sm.add("SourceD", "https://d.example.com/simple")
        sources = sm.load()
        assert len(sources) == 4
        assert sources[3]["name"] == "SourceD"
        assert sources[3]["enabled"] is True  # new sources default enabled

    def test_remove_source(self, temp_config):
        sm = SourceManager(temp_config)
        sm.remove(0)  # remove SourceA
        sources = sm.load()
        assert len(sources) == 2
        assert sources[0]["name"] == "SourceB"

    def test_remove_source_out_of_range(self, temp_config):
        sm = SourceManager(temp_config)
        sm.remove(99)  # should not raise
        sources = sm.load()
        assert len(sources) == 3

    def test_move_up(self, temp_config):
        sm = SourceManager(temp_config)
        sm.move_up(1)  # move SourceB (index 1) up
        sources = sm.load()
        assert sources[0]["name"] == "SourceB"
        assert sources[1]["name"] == "SourceA"

    def test_move_up_first_does_nothing(self, temp_config):
        sm = SourceManager(temp_config)
        sm.move_up(0)
        sources = sm.load()
        assert sources[0]["name"] == "SourceA"  # unchanged

    def test_move_down(self, temp_config):
        sm = SourceManager(temp_config)
        sm.move_down(1)  # move SourceB (index 1) down
        sources = sm.load()
        assert sources[1]["name"] == "SourceC"
        assert sources[2]["name"] == "SourceB"

    def test_move_down_last_does_nothing(self, temp_config):
        sm = SourceManager(temp_config)
        sm.move_down(2)  # last element
        sources = sm.load()
        assert sources[2]["name"] == "SourceC"  # unchanged

    def test_toggle(self, temp_config):
        sm = SourceManager(temp_config)
        sm.toggle(0)  # toggle SourceA from True to False
        sources = sm.load()
        assert sources[0]["enabled"] is False

        sm.toggle(0)  # toggle back
        sources = sm.load()
        assert sources[0]["enabled"] is True

    def test_save_persists(self, temp_config):
        sm = SourceManager(temp_config)
        sm.add("NewSource", "https://new.example.com/simple")
        sm.toggle(0)

        # Reload from file
        sm2 = SourceManager(temp_config)
        sources = sm2.load()
        assert len(sources) == 4
        assert sources[0]["enabled"] is False
        assert sources[3]["name"] == "NewSource"

    def test_missing_file_creates_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = str(Path(tmpdir) / "nonexistent.json")
            sm = SourceManager(config_path)
            sources = sm.load()
            # Should have default sources or empty list
            assert isinstance(sources, list)
            # File should be created
            assert Path(config_path).exists()

    @patch("urllib.request.urlopen")
    def test_test_connection_success(self, mock_urlopen, temp_config):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        sm = SourceManager(temp_config)
        ok, msg = sm.test_connection("https://pypi.org/simple")
        assert ok is True
        assert "成功" in msg or "OK" in msg.upper()

    @patch("urllib.request.urlopen")
    def test_test_connection_failure(self, mock_urlopen, temp_config):
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("timeout")

        sm = SourceManager(temp_config)
        ok, msg = sm.test_connection("https://bad.example.com/simple")
        assert ok is False

    @patch("urllib.request.urlopen")
    def test_test_connection_http_error(self, mock_urlopen, temp_config):
        from urllib.error import HTTPError
        mock_response = MagicMock()
        mock_response.status = 404
        mock_urlopen.side_effect = HTTPError(
            "https://bad.example.com/simple", 404, "Not Found", {}, mock_response
        )

        sm = SourceManager(temp_config)
        ok, msg = sm.test_connection("https://bad.example.com/simple")
        assert ok is False
