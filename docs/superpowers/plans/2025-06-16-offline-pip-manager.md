# Offline Pip Manager — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CustomTkinter GUI app to download/install Python packages offline on Windows, with auto source failover.

**Architecture:** Tab-based GUI (下载/本地包管理/离线安装/源管理) backed by a pip-subprocess core. pip download for online fetching, pip install --no-index for offline install, PyPI JSON API for version checks.

**Tech Stack:** Python 3.10+, CustomTkinter, pip (subprocess), packaging, PyInstaller for build

---

### Task 1: Project Scaffolding

**Files:**
- Create: `offline_pip_manager/requirements.txt`
- Create: `offline_pip_manager/config.json`
- Create: `offline_pip_manager/core/__init__.py`
- Create: `offline_pip_manager/ui/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
customtkinter>=5.2.0
packaging>=23.0
```

- [ ] **Step 2: Create default config.json**

```json
{
  "store_directory": "./offline_packages",
  "sources": [
    {"name": "清华", "url": "https://pypi.tuna.tsinghua.edu.cn/simple", "enabled": true},
    {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple", "enabled": true},
    {"name": "中科大", "url": "https://pypi.mirrors.ustc.edu.cn/simple", "enabled": true},
    {"name": "豆瓣", "url": "https://pypi.douban.com/simple", "enabled": false},
    {"name": "华为云", "url": "https://repo.huaweicloud.com/repository/pypi/simple", "enabled": false},
    {"name": "PyPI官方", "url": "https://pypi.org/simple", "enabled": true}
  ],
  "download_with_deps": true,
  "timeout_seconds": 30,
  "theme": "dark"
}
```

- [ ] **Step 3: Create empty __init__.py files**

- [ ] **Step 4: Install dependencies**

Run: `uv pip install -r requirements.txt`
Expected: customtkinter and packaging installed

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/
git commit -m "chore: scaffold project structure"
```

---

### Task 2: Core — Source Manager

**Files:**
- Create: `offline_pip_manager/core/source_manager.py`
- Create: `tests/test_source_manager.py`

**Interface:**
```python
class SourceManager:
    def __init__(self, config_path: str): ...
    def load(self) -> list[dict]: ...
    def save(self, sources: list[dict]) -> None: ...
    def get_enabled(self) -> list[dict]: ...
    def add(self, name: str, url: str) -> None: ...
    def remove(self, index: int) -> None: ...
    def move_up(self, index: int) -> None: ...
    def move_down(self, index: int) -> None: ...
    def toggle(self, index: int) -> None: ...
    def test_connection(self, url: str, timeout: int = 10) -> tuple[bool, str]: ...
```

- [ ] **Step 1: Write tests for source_manager**

Test: load default config, get_enabled returns only enabled sources, add/remove/toggle/move operations, save preserves order, test_connection (mock requests), config file missing creates default.

- [ ] **Step 2: Run tests, verify they fail**

Run: `pytest tests/test_source_manager.py -v`
Expected: all FAIL (module not found)

- [ ] **Step 3: Implement source_manager.py**

Implement all methods. `test_connection` uses `urllib.request.urlopen` with a HEAD/GET to the simple index URL. Config uses default if file missing.

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_source_manager.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/core/source_manager.py tests/test_source_manager.py
git commit -m "feat: source manager with CRUD and connection testing"
```

---

### Task 3: Core — Package Index (Local Scanner)

**Files:**
- Create: `offline_pip_manager/core/package_index.py`
- Create: `tests/test_package_index.py`

**Interface:**
```python
def scan_directory(directory: str) -> list[dict]:
    """Scan directory for .whl and .tar.gz files.
    Returns: [{name, version, filename, path, size, date}, ...]
    """
```

- [ ] **Step 1: Write tests**

Create temp dir with sample .whl files, scan, verify parsed name/version. Empty dir returns empty list. Non-existent dir raises FileNotFoundError.

- [ ] **Step 2: Run tests, verify fail**

- [ ] **Step 3: Implement package_index.py**

Use `packaging.utils.parse_wheel_filename` for .whl files, regex fallback for .tar.gz. Use `os.path.getsize` / `os.path.getmtime` for size and date.

- [ ] **Step 4: Run tests, verify pass**

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/core/package_index.py tests/test_package_index.py
git commit -m "feat: local package index scanner"
```

---

### Task 4: Core — Downloader

**Files:**
- Create: `offline_pip_manager/core/downloader.py`
- Create: `tests/test_downloader.py`

**Interface:**
```python
class Downloader:
    def __init__(self, source_manager: SourceManager, store_dir: str, timeout: int = 30): ...
    def download(self, package: str, version: str | None = None, with_deps: bool = True,
                 on_progress: Callable = None, on_log: Callable = None) -> bool: ...
```

- [ ] **Step 1: Write tests**

Mock subprocess to simulate pip download success/failure. Test auto-failover: first source fails → tries second → succeeds. All sources fail → returns False. Version pin behavior. with_deps=False adds --no-deps flag. Progress/log callbacks invoked.

- [ ] **Step 2: Run tests, verify fail**

- [ ] **Step 3: Implement downloader.py**

Uses `subprocess.Popen` to run `pip download package[==version] -d store_dir [-i source_url] [--no-deps]`. Iterates enabled sources from SourceManager. On failure (non-zero exit or timeout), logs and tries next. Calls on_progress/on_log callbacks. Streams stdout line by line via `readline()` in a thread to prevent UI freeze.

- [ ] **Step 4: Run tests, verify pass**

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/core/downloader.py tests/test_downloader.py
git commit -m "feat: pip downloader with auto source failover"
```

---

### Task 5: Core — Installer

**Files:**
- Create: `offline_pip_manager/core/installer.py`
- Create: `tests/test_installer.py`

**Interface:**
```python
class Installer:
    def __init__(self, store_dir: str, python_path: str = "python"): ...
    def install(self, packages: list[str], on_log: Callable = None) -> bool: ...
```

- [ ] **Step 1: Write tests**

Mock subprocess. Test: install succeeds, install fails with error output, --no-index and --find-links flags present, custom python_path used.

- [ ] **Step 2: Run tests, verify fail**

- [ ] **Step 3: Implement installer.py**

Runs: `python_path -m pip install --no-index --find-links store_dir pkg1 pkg2...`
Streams output via callback.

- [ ] **Step 4: Run tests, verify pass**

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/core/installer.py tests/test_installer.py
git commit -m "feat: offline installer via pip --no-index"
```

---

### Task 6: Core — Version Checker

**Files:**
- Create: `offline_pip_manager/core/checker.py`
- Create: `tests/test_checker.py`

**Interface:**
```python
class VersionChecker:
    def __init__(self, source_manager: SourceManager, timeout: int = 15): ...
    def check_package(self, name: str, local_version: str) -> dict | None:
        """Returns {'name':, 'local':, 'latest':, 'has_update':} or None on error"""
    def check_all(self, packages: list[dict]) -> list[dict]: ...
```

- [ ] **Step 1: Write tests**

Mock urllib to return PyPI JSON. Test: local older → has_update=True, local newest → has_update=False, network error → returns None, check_all returns list with status per package.

- [ ] **Step 2: Run tests, verify fail**

- [ ] **Step 3: Implement checker.py**

Uses `urllib.request.urlopen` to GET `https://pypi.org/pypi/{name}/json` (tries enabled sources in order). Parses JSON `info.version`. Compares with `packaging.version.parse`.

- [ ] **Step 4: Run tests, verify pass**

- [ ] **Step 5: Commit**

```bash
git add offline_pip_manager/core/checker.py tests/test_checker.py
git commit -m "feat: version checker against PyPI"
```

---

### Task 7: UI — Main Application Window

**Files:**
- Create: `offline_pip_manager/app.py`

- [ ] **Step 1: Write app.py**

```python
import customtkinter as ctk
from pathlib import Path
from core.source_manager import SourceManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("离线 Pip 包管理器")
        self.geometry("900x650")
        
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
        # TabView
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("下载")
        self.tabview.add("本地包管理")
        self.tabview.add("离线安装")
        self.tabview.add("源管理")
        
        # Import and init tabs (placeholders for now)
        from ui.download_tab import DownloadTab
        from ui.local_tab import LocalTab
        from ui.install_tab import InstallTab
        from ui.source_tab import SourceTab
        
        self.download_tab = DownloadTab(self.tabview.tab("下载"), self)
        self.local_tab = LocalTab(self.tabview.tab("本地包管理"), self)
        self.install_tab = InstallTab(self.tabview.tab("离线安装"), self)
        self.source_tab = SourceTab(self.tabview.tab("源管理"), self)
        
        # Status bar
        self.status_bar = ctk.CTkLabel(self, text="就绪", anchor="w")
        self.status_bar.pack(fill="x", padx=10, pady=(0, 5))
    
    def set_status(self, text: str):
        self.status_bar.configure(text=text)
    
    def _load_config(self, path: Path) -> dict:
        import json
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
```

- [ ] **Step 2: Verify app can import without errors**

Run: `cd offline_pip_manager && python -c "from app import App; print('OK')"`
Expected: OK (import succeeds even if tabs are stubs)

- [ ] **Step 3: Commit**

```bash
git add offline_pip_manager/app.py
git commit -m "feat: main application window with tabview"
```

---

### Task 8: UI — Source Management Tab

**Files:**
- Create: `offline_pip_manager/ui/source_tab.py`

- [ ] **Step 1: Implement source_tab.py**

Layout:
- Top: explanatory label
- Middle: scrollable frame with rows: index | checkbox | name | URL
- Bottom: [添加] [删除] [↑上移] [↓下移] [测试连接] buttons
- Add dialog: popup with name + URL fields
- Test connection: runs SourceManager.test_connection, shows result in a messagebox

Key methods:
- `_refresh_list()` — rebuilds the scrollable frame from source_manager
- `_add_source()` — CTkInputDialog for name/url
- `_remove_source()` — removes selected, refresh
- `_move_up()` / `_move_down()` — reorder, refresh
- `_test_connection()` — test selected source URL
- `_on_toggle(index)` — toggle enabled status, save

- [ ] **Step 2: Run app, visually verify source tab**

Run: `python main.py`
Expected: Tab shows 6 pre-configured sources, checkboxes work, buttons work

- [ ] **Step 3: Commit**

```bash
git add offline_pip_manager/ui/source_tab.py
git commit -m "feat: source management tab UI"
```

---

### Task 9: UI — Download Tab

**Files:**
- Create: `offline_pip_manager/ui/download_tab.py`

- [ ] **Step 1: Implement download_tab.py**

Layout:
- Search row: entry + button
- Search results: label showing package name + version dropdown + description
- Action buttons: [下载包及所有依赖] [仅下载包本身]
- Download log: CTkTextbox (read-only)
- Progress bar: CTkProgressBar

Key methods:
- `_search()` — use urllib to query PyPI JSON for package info, populate dropdown
- `_on_download(with_deps)` — spawn thread: Downloader.download(..., on_log=self._append_log, on_progress=self._update_progress)
- `_append_log(line)` — thread-safe log append
- `_update_progress(value)` — thread-safe progress update

Thread safety: use `self.after(0, callback)` to update UI from background thread.

- [ ] **Step 2: Run app, visually verify download tab**

Run: `python main.py`
Expected: Search "openpyxl", see version dropdown, click download, see log and progress

- [ ] **Step 3: Commit**

```bash
git add offline_pip_manager/ui/download_tab.py
git commit -m "feat: download tab with search and progress"
```

---

### Task 10: UI — Local Package Management Tab

**Files:**
- Create: `offline_pip_manager/ui/local_tab.py`

- [ ] **Step 1: Implement local_tab.py**

Layout:
- Top row: store directory entry + [浏览...] button
- Package table: scrollable frame with columns: 包名 | 版本 | 大小 | 日期 | 状态
- Action bar: [全选] [检查更新] [删除选中] [刷新]
- Status column: "● 已是最新" (green) / "▲ 有更新: x.y.z" (orange) / "— 未检查" (grey)

Key methods:
- `_refresh()` — scan store_dir via package_index, populate table
- `_browse_directory()` — filedialog.askdirectory
- `_check_updates()` — spawn thread: VersionChecker.check_all(), update status column with colors
- `_delete_selected()` — confirm dialog, delete files, refresh
- `_select_all()` — toggle all checkboxes (checkbox column per row)

Each row in the scrollable frame:
```
[☐] openpyxl    3.1.5    250KB    2025-06-16    ● 已是最新
```

- [ ] **Step 2: Run app, visually verify local tab**

Run: `python main.py`
Expected: Shows packages in store_dir, check updates highlights stale packages

- [ ] **Step 3: Commit**

```bash
git add offline_pip_manager/ui/local_tab.py
git commit -m "feat: local package management tab"
```

---

### Task 11: UI — Offline Install Tab

**Files:**
- Create: `offline_pip_manager/ui/install_tab.py`

- [ ] **Step 1: Implement install_tab.py**

Layout:
- Store directory row: entry + [浏览...]
- Target Python row: entry (default "python") + [浏览...] (file dialog for python.exe)
- Package checklist: scrollable frame with checkboxes per package (populated from store_dir)
- Action buttons: [安装选中的包] [全选] [取消全选]
- Install log: CTkTextbox (read-only)

Key methods:
- `_refresh()` — scan store_dir, populate checklist
- `_install()` — confirm dialog listing packages to install → spawn thread: Installer.install(pkg_names, on_log=self._append_log)
- `_browse_python()` — filedialog.askopenfilename for python.exe
- `_select_all()` / `_deselect_all()`

- [ ] **Step 2: Run app, visually verify install tab**

Run: `python main.py`
Expected: Shows packages from store_dir, check some, click install, see pip output in log

- [ ] **Step 3: Commit**

```bash
git add offline_pip_manager/ui/install_tab.py
git commit -m "feat: offline install tab"
```

---

### Task 12: Entry Point & Integration

**Files:**
- Create: `offline_pip_manager/main.py`

- [ ] **Step 1: Write main.py**

```python
import sys
import os

# Ensure we can find pip
def check_pip():
    import subprocess
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if __name__ == "__main__":
    if not check_pip():
        import tkinter.messagebox as mb
        mb.showerror("错误", "未找到 pip。请确保 Python 已正确安装并添加到 PATH。")
        sys.exit(1)
    
    from app import App
    app = App()
    app.mainloop()
```

- [ ] **Step 2: Full integration test**

Run: `cd offline_pip_manager && python main.py`
Expected: Full app launches, all tabs functional. Test download → check local → install offline cycle with a simple package.

- [ ] **Step 3: Fix any issues found during integration**

- [ ] **Step 4: Commit**

```bash
git add offline_pip_manager/main.py
git commit -m "feat: entry point with pip check"
```

---

### Task 13: PyInstaller Build Script

**Files:**
- Create: `offline_pip_manager/build.py`
- Modify: `offline_pip_manager/main.py` (add required hooks if needed)

- [ ] **Step 1: Write build.py**

```python
"""Build script for PyInstaller single-exe packaging."""
import subprocess
import sys
from pathlib import Path

def build():
    root = Path(__file__).parent
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",  # no console window
        "--name", "离线pip包管理器",
        "--add-data", f"{root / 'config.json'};.",
        "--hidden-import", "customtkinter",
        str(root / "main.py")
    ]
    subprocess.run(cmd, cwd=str(root), check=True)
    print(f"Build complete: {root / 'dist' / '离线pip包管理器.exe'}")

if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Install PyInstaller and build**

Run: `uv pip install pyinstaller && cd offline_pip_manager && python build.py`
Expected: dist/离线pip包管理器.exe created, runs without console

- [ ] **Step 3: End-to-end test with built exe**

- Test download: search a package on external network → download success
- Test local management: check updates, delete
- Test install: copy exe + offline_packages folder to another location → install works

- [ ] **Step 4: Commit**

```bash
git add offline_pip_manager/build.py
git commit -m "feat: pyinstaller build script"
```

---

## Testing Summary

| Layer | Tests | Type |
|-------|-------|------|
| `source_manager` | CRUD, enable/disable, connection test | Unit (pytest) |
| `package_index` | Scan dir, parse wheel names | Unit (pytest) |
| `downloader` | Failover, flags, callbacks | Unit (pytest + mock) |
| `installer` | --no-index, custom python, log | Unit (pytest + mock) |
| `checker` | Version compare, network error | Unit (pytest + mock) |
| UI tabs | Visual inspection | Manual |
| Full app | Download → install cycle | Manual integration |
