"""Tests for core.installer."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "offline_pip_manager"))

from core.installer import Installer


def _mock_popen_success(*args, **kwargs):
    mock = MagicMock()
    mock.returncode = 0
    mock.stdout.readline.side_effect = [
        "Processing ./packages/requests-2.31.0.whl",
        "Installing collected packages: requests",
        "Successfully installed requests-2.31.0",
        "",
    ]
    mock.poll.return_value = 0
    mock.wait.return_value = 0
    return mock


def _mock_popen_failure(*args, **kwargs):
    mock = MagicMock()
    mock.returncode = 1
    mock.stdout.readline.side_effect = [
        "ERROR: No matching distribution found",
        "",
    ]
    mock.poll.return_value = 1
    mock.wait.return_value = 1
    return mock


class TestInstaller:

    @patch("subprocess.Popen")
    def test_install_success(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("./packages")
        logs = []
        result = installer.install(["requests", "numpy"], on_log=logs.append)

        assert result is True
        assert len(logs) > 0

    @patch("subprocess.Popen")
    def test_install_no_index_flag(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("./offline_packages")
        installer.install(["requests"])

        cmd_args = mock_popen.call_args[0][0]
        assert "--no-index" in cmd_args

    @patch("subprocess.Popen")
    def test_install_find_links_flag(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("/custom/store")
        installer.install(["requests"])

        cmd_args = mock_popen.call_args[0][0]
        assert "--find-links" in cmd_args
        assert "/custom/store" in cmd_args

    @patch("subprocess.Popen")
    def test_install_custom_python_path(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("./pkgs", python_path="C:\\Python313\\python.exe")
        installer.install(["requests"])

        cmd_args = mock_popen.call_args[0][0]
        assert cmd_args[0] == "C:\\Python313\\python.exe"

    @patch("subprocess.Popen")
    def test_install_default_python(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("./pkgs")  # default python_path="python"
        installer.install(["requests"])

        cmd_args = mock_popen.call_args[0][0]
        assert cmd_args[0] == "python"

    @patch("subprocess.Popen")
    def test_install_failure(self, mock_popen):
        mock_popen.return_value = _mock_popen_failure()

        installer = Installer("./pkgs")
        logs = []
        result = installer.install(["bad-package"], on_log=logs.append)

        assert result is False

    @patch("subprocess.Popen")
    def test_install_log_output(self, mock_popen):
        mock_popen.return_value = _mock_popen_success()

        installer = Installer("./pkgs")
        logs = []
        installer.install(["requests"], on_log=logs.append)

        assert any("requests" in line for line in logs)
