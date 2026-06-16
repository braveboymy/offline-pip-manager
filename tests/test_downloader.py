"""Tests for core.downloader."""

import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "offline_pip_manager"))

from core.downloader import Downloader
from core.source_manager import SourceManager


@pytest.fixture
def source_manager():
    """Create a SourceManager with test config."""
    import tempfile
    import json
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({
            "sources": [
                {"name": "Mirror1", "url": "https://mirror1.example.com/simple", "enabled": True},
                {"name": "Mirror2", "url": "https://mirror2.example.com/simple", "enabled": True},
                {"name": "Disabled", "url": "https://disabled.example.com/simple", "enabled": False},
            ]
        }, f)
        path = f.name
    sm = SourceManager(path)
    yield sm
    Path(path).unlink(missing_ok=True)


class TestDownloader:

    def _mock_popen_success(self, *args, **kwargs):
        """Return a mock Popen that succeeds."""
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout.readline.side_effect = [
            "Collecting requests",
            "  Downloading requests-2.31.0.whl",
            "Successfully downloaded requests",
            "",  # EOF sentinel
        ]
        mock.poll.return_value = 0
        mock.wait.return_value = 0
        return mock

    def _mock_popen_failure(self, *args, **kwargs):
        """Return a mock Popen that fails."""
        mock = MagicMock()
        mock.returncode = 1
        mock.stdout.readline.side_effect = [
            "ERROR: Could not find a version",
            "",  # EOF sentinel
        ]
        mock.poll.return_value = 1
        mock.wait.return_value = 1
        return mock

    @patch("subprocess.Popen")
    def test_download_success(self, mock_popen, source_manager, tmp_path):
        mock_popen.return_value = self._mock_popen_success()

        store_dir = str(tmp_path / "packages")
        os.makedirs(store_dir, exist_ok=True)

        downloader = Downloader(source_manager, store_dir, timeout=30)
        logs = []
        result = downloader.download("requests", version="2.31.0", on_log=logs.append)

        assert result is True
        assert len(logs) > 0
        assert any("requests" in line for line in logs)

    @patch("subprocess.Popen")
    def test_download_without_version(self, mock_popen, source_manager, tmp_path):
        mock_popen.return_value = self._mock_popen_success()

        downloader = Downloader(source_manager, str(tmp_path))
        result = downloader.download("requests", version=None)
        assert result is True

        # Check command doesn't include ==
        cmd_args = mock_popen.call_args[0][0]
        assert "requests" in cmd_args
        assert "==" not in " ".join(cmd_args)

    @patch("subprocess.Popen")
    def test_download_without_deps_adds_no_deps_flag(self, mock_popen, source_manager, tmp_path):
        mock_popen.return_value = self._mock_popen_success()

        downloader = Downloader(source_manager, str(tmp_path))
        result = downloader.download("requests", with_deps=False)
        assert result is True

        cmd_args = mock_popen.call_args[0][0]
        assert "--no-deps" in cmd_args

    @patch("subprocess.Popen")
    def test_download_with_deps_default(self, mock_popen, source_manager, tmp_path):
        mock_popen.return_value = self._mock_popen_success()

        downloader = Downloader(source_manager, str(tmp_path))
        result = downloader.download("requests")
        assert result is True

        cmd_args = mock_popen.call_args[0][0]
        assert "--no-deps" not in cmd_args

    @patch("subprocess.Popen")
    def test_failover_to_second_source(self, mock_popen, source_manager, tmp_path):
        """First source fails, second succeeds."""
        fail_mock = self._mock_popen_failure()
        success_mock = self._mock_popen_success()
        mock_popen.side_effect = [fail_mock, success_mock]

        downloader = Downloader(source_manager, str(tmp_path))
        logs = []
        result = downloader.download("requests", on_log=logs.append)

        assert result is True
        assert mock_popen.call_count == 2
        # Should have tried mirror1 first, then mirror2
        first_call = " ".join(mock_popen.call_args_list[0][0][0])
        second_call = " ".join(mock_popen.call_args_list[1][0][0])
        assert "mirror1" in first_call
        assert "mirror2" in second_call

    @patch("subprocess.Popen")
    def test_all_sources_fail(self, mock_popen, source_manager, tmp_path):
        """All sources fail → returns False."""
        fail1 = self._mock_popen_failure()
        fail2 = self._mock_popen_failure()
        mock_popen.side_effect = [fail1, fail2]

        downloader = Downloader(source_manager, str(tmp_path))
        result = downloader.download("nonexistent")

        assert result is False
        assert mock_popen.call_count == 2  # tried both enabled sources

    @patch("subprocess.Popen")
    def test_progress_callback(self, mock_popen, source_manager, tmp_path):
        mock_popen.return_value = self._mock_popen_success()

        downloader = Downloader(source_manager, str(tmp_path))
        progress_values = []
        log_lines = []
        result = downloader.download(
            "requests",
            on_progress=lambda p: progress_values.append(p),
            on_log=lambda l: log_lines.append(l),
        )
        assert result is True
        assert len(log_lines) > 0
