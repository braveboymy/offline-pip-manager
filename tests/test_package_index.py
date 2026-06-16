"""Tests for core.package_index."""

import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "offline_pip_manager"))

from core.package_index import scan_directory


@pytest.fixture
def temp_packages_dir():
    """Create a temp directory with sample wheel files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some fake wheel and tar.gz files
        files = [
            "openpyxl-3.1.5-py2.py3-none-any.whl",
            "et_xmlfile-2.0.0-py3-none-any.whl",
            "numpy-2.1.0-cp313-cp313-win_amd64.whl",
            "requests-2.31.0.tar.gz",
            "not_a_package.txt",  # should be ignored
        ]
        for fname in files:
            path = Path(tmpdir) / fname
            path.write_text("dummy content")
            # Set a specific mtime
            os.utime(path, (1000000, 1000000))

        yield tmpdir


class TestScanDirectory:

    def test_scans_wheels_and_tarballs(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        assert len(results) == 4  # 4 valid packages, not the .txt

        names = {r["name"] for r in results}
        assert names == {"openpyxl", "et-xmlfile", "numpy", "requests"}

    def test_parses_name_and_version(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        by_name = {r["name"]: r for r in results}

        assert by_name["openpyxl"]["version"] == "3.1.5"
        assert by_name["et-xmlfile"]["version"] == "2.0.0"
        assert by_name["numpy"]["version"] == "2.1.0"
        assert by_name["requests"]["version"] == "2.31.0"

    def test_includes_filename_and_path(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        by_name = {r["name"]: r for r in results}

        assert by_name["openpyxl"]["filename"] == "openpyxl-3.1.5-py2.py3-none-any.whl"
        assert str(by_name["openpyxl"]["path"]).endswith("openpyxl-3.1.5-py2.py3-none-any.whl")

    def test_includes_size(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        for r in results:
            assert r["size"] > 0
            assert isinstance(r["size"], int)

    def test_includes_date(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        for r in results:
            assert "date" in r
            assert isinstance(r["date"], str)

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = scan_directory(tmpdir)
            assert results == []

    def test_nonexistent_directory(self):
        with pytest.raises(FileNotFoundError):
            scan_directory("/nonexistent/path/xyz")

    def test_results_sorted_by_name(self, temp_packages_dir):
        results = scan_directory(temp_packages_dir)
        names = [r["name"] for r in results]
        assert names == sorted(names)
