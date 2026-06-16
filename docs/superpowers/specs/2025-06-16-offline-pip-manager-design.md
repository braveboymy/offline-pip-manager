# Offline Pip Manager — Design Spec

**Date:** 2025-06-16  
**Status:** Draft  
**Target:** Windows-only, Python desktop GUI app

---

## 1. Overview

A desktop GUI tool that lets users download Python packages (with dependencies) on an internet-connected Windows machine, then install them from local storage on an air-gapped Windows machine.

**Key decisions:**
- GUI Framework: **CustomTkinter** (modern flat UI, zero extra runtime dependencies)
- Package backend: **pip** (`pip download` / `pip install --no-index`), no uv dependency
- Platform: **Windows only**, packaged as single `.exe` via PyInstaller
- Structure: **Tab-based** (4 tabs)

---

## 2. Architecture

```
┌─────────────────────────────────────────────┐
│  Tab: 下载 │ 本地包管理 │ 离线安装 │ 源管理   │
├─────────────────────────────────────────────┤
│                                             │
│   [当前活跃面板内容区]                        │
│                                             │
├─────────────────────────────────────────────┤
│  状态栏：当前存储目录 │ 包数量 │ 上次刷新      │
└─────────────────────────────────────────────┘
```

### 2.1 Module Breakdown

| Module | Responsibility | Dependencies |
|--------|---------------|--------------|
| `app.py` | Main window, TabView, status bar, global state | CTk, ui/* |
| `ui/download_tab.py` | Search, version pick, download button, progress, log | core/downloader |
| `ui/local_tab.py` | Local package list, check-updates, delete, refresh | core/checker, core/package_index |
| `ui/install_tab.py` | Offline install UI: env picker, package checklist, install log | core/installer, core/package_index |
| `ui/source_tab.py` | Source list CRUD, enable/disable, reorder, test-connect | core/source_manager |
| `core/downloader.py` | `pip download` wrapper with auto-source-failover | core/source_manager |
| `core/installer.py` | `pip install --no-index --find-links <dir>` wrapper | — |
| `core/checker.py` | Compare local wheel versions against PyPI (JSON API) | core/source_manager |
| `core/source_manager.py` | CRUD for source list, persist to config.json, failover logic | — |
| `core/package_index.py` | Scan local directory for wheel files, return structured list | — |

### 2.2 Data Flow

**Download flow:**
```
User: search "openpyxl", pick version → download_tab
  → downloader.download(pkg, version, store_dir, source_list)
    → for source in source_list (by priority):
        → subprocess: pip download pkg==ver -d store_dir -i source_url
        → if success: break
        → if fail: next source
    → log progress to UI
    → status bar updates count
```

**Check-updates flow:**
```
User: click "检查更新" on local_tab
  → checker.check_updates(store_dir)
    → package_index.scan(store_dir) → local packages
    → for each pkg: fetch PyPI JSON API → latest version
    → compare local vs remote → return diff list
  → UI highlights: green (current) / orange (update available)
```

**Install flow:**
```
User: select packages, choose env, click "安装"
  → installer.install(pkg_paths, target_python)
    → subprocess: pip install --no-index --find-links store_dir pkg1 pkg2...
    → log to UI
```

---

## 3. UI Details

### 3.1 Download Tab

```
┌─────────────────────────────────────────────┐
│ 搜索包名: [_______________] [搜索]           │
│ ───────────────────────────────             │
│ 搜索结果: openpyxl                          │
│   版本: [3.1.5 ▼]                           │
│   描述: A Python library to read/write...   │
│                                             │
│ [下载包及所有依赖]  [仅下载包本身]           │
│ ───────────────────────────────             │
│ 下载日志:                                   │
│ Collecting openpyxl==3.1.5...               │
│   Downloading openpyxl-3.1.5-...whl         │
│ Collecting et_xmlfile...                    │
│ ...                                         │
│ 进度: [████████████────] 80%               │
│ 状态: 下载中...                             │
└─────────────────────────────────────────────┘
```

### 3.2 Local Package Management Tab

```
┌─────────────────────────────────────────────┐
│ 存储目录: [C:\offline_pkgs] [浏览...]       │
│ ───────────────────────────────             │
│ 包名        版本    大小    日期    状态     │
│ openpyxl    3.1.5   250KB  06-16  ● 已是最新│
│ et_xmlfile  2.0.0   18KB   06-16  ▲ 有更新  │
│ numpy       2.1.0   16MB   06-15  ● 已是最新│
│ ───────────────────────────────             │
│ [全选] [检查更新] [删除选中] [刷新]         │
└─────────────────────────────────────────────┘
```

### 3.3 Offline Install Tab

```
┌─────────────────────────────────────────────┐
│ 包存储目录: [C:\offline_pkgs] [浏览...]     │
│ 目标环境:   [python.exe路径] [浏览...]      │
│ ───────────────────────────────             │
│ [☑] openpyxl 3.1.5                          │
│ [☑] et_xmlfile 2.0.0                        │
│ [ ] numpy 2.1.0                             │
│ ───────────────────────────────             │
│ [安装选中的包]  [全选] [取消全选]           │
│ ───────────────────────────────             │
│ 安装日志:                                   │
│ Installing collected packages...            │
│ Successfully installed openpyxl-3.1.5...    │
└─────────────────────────────────────────────┘
```

### 3.4 Source Management Tab

```
┌─────────────────────────────────────────────┐
│ 镜像源管理                                   │
│ ───────────────────────────────             │
│ 序号  启用  源名称        URL               │
│  1   [☑]  清华         https://pypi.tuna... │
│  2   [☑]  阿里云       https://mirrors.a... │
│  3   [ ]  官方         https://pypi.org/s...│
│  4   [☑]  自定义      https://mymirror...   │
│ ───────────────────────────────             │
│ [添加] [删除] [↑上移] [↓下移] [测试连接]    │
└─────────────────────────────────────────────┘
```

---

## 4. Error Handling & Edge Cases

### 4.1 Auto Source Failover
- Download tries each enabled source in priority order
- On network error / timeout / 4xx/5xx, logs the failure and moves to next source
- If all sources fail: shows error dialog with per-source failure details
- Timeout per source: 30s (configurable)

### 4.2 Permission / Environment Issues
- No pip found: show error with instructions to install Python
- No write permission to store_dir: show error with path
- Target Python env not found: validate path before install
- Corrupt wheel files: pip will report, shown in log

### 4.3 Edge Cases
- Store directory empty → show "暂无包文件" placeholder
- Package not found on PyPI → show "未找到该包" message
- Version conflicts during download: pip resolves naturally, log shows warnings
- Large downloads: streaming log to prevent UI freeze (background thread)
- Unicode characters in package names or paths: use subprocess with proper encoding

---

## 5. Configuration

`config.json` stored beside the exe:

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

---

## 6. Build & Distribution

- **Build tool:** PyInstaller, single `.exe` (--onefile)
- **Entry point:** `main.py`
- **Bundled assets:** icon (optional)
- **Output:** `dist/离线pip包管理器.exe`
- **Dependencies:** customtkinter, packaging (for version parsing)
- **Runtime only:** Python 3.10+ must be installed on target machine (for pip)

---

## 7. Project File Tree

```
offline_pip_manager/
├── main.py
├── app.py
├── ui/
│   ├── __init__.py
│   ├── download_tab.py
│   ├── local_tab.py
│   ├── install_tab.py
│   └── source_tab.py
├── core/
│   ├── __init__.py
│   ├── downloader.py
│   ├── installer.py
│   ├── checker.py
│   ├── source_manager.py
│   └── package_index.py
├── config.json
└── build.py
```
