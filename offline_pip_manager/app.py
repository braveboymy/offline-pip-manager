"""Main application window with tab-based navigation."""

import json
from pathlib import Path

import customtkinter as ctk

from core.source_manager import SourceManager


class App(ctk.CTk):
    """Main application window for Offline Pip Manager."""

    def __init__(self):
        super().__init__()

        self.title("离线 Pip 包管理器")
        self.geometry("960x680")
        self.minsize(800, 550)

        # Load config
        config_path = Path(__file__).parent / "config.json"
        self.source_manager = SourceManager(str(config_path))
        self.config = self._load_config(config_path)

        # Apply theme
        ctk.set_appearance_mode(self.config.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        # Store directory
        self.store_dir = self.config.get("store_directory", "./offline_packages")
        Path(self.store_dir).mkdir(parents=True, exist_ok=True)

        self._build_ui()

    def _build_ui(self):
        """Build the main UI structure."""
        # Status bar (must be created before tabs, as tabs call set_status)
        self.status_var = ctk.StringVar(value="就绪")
        self.status_bar = ctk.CTkLabel(
            self, textvariable=self.status_var, anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 8))

        # TabView
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tabview.add("下载")
        self.tabview.add("本地包管理")
        self.tabview.add("离线安装")
        self.tabview.add("源管理")

        # Import and init tabs
        from ui.download_tab import DownloadTab
        from ui.local_tab import LocalTab
        from ui.install_tab import InstallTab
        from ui.source_tab import SourceTab

        self.download_tab = DownloadTab(self.tabview.tab("下载"), self)
        self.local_tab = LocalTab(self.tabview.tab("本地包管理"), self)
        self.install_tab = InstallTab(self.tabview.tab("离线安装"), self)
        self.source_tab = SourceTab(self.tabview.tab("源管理"), self)

    def set_status(self, text: str):
        """Update the status bar text."""
        self.status_var.set(text)

    def _load_config(self, path: Path) -> dict:
        """Load config JSON, return empty dict if missing."""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
