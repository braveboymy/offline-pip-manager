"""Download tab — search packages and download with dependencies."""

import json
import threading
import urllib.request
import urllib.error

import customtkinter as ctk
from tkinter import messagebox

from core.downloader import Downloader


class DownloadTab:
    """Tab for searching and downloading Python packages."""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._search_results: list[dict] = []
        self._downloading = False

        self._build_ui()

    def _build_ui(self):
        """Build the download tab UI."""
        # Header
        header = ctk.CTkLabel(
            self.parent, text="下载 Python 包",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(pady=(10, 5), anchor="w")

        desc = ctk.CTkLabel(
            self.parent,
            text="搜索并下载 Python 包及其依赖到本地存储目录，用于离线迁移。",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(pady=(0, 10), anchor="w")

        # Store directory
        dir_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        dir_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(dir_frame, text="存储目录:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.dir_entry = ctk.CTkEntry(dir_frame)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.dir_entry.insert(0, self.app.store_dir)
        ctk.CTkButton(dir_frame, text="浏览", width=60, command=self._browse_dir).pack(side="right")

        # Search bar
        search_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        search_frame.pack(fill="x", padx=5, pady=(10, 2))
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="输入包名搜索...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._search())
        self.search_btn = ctk.CTkButton(search_frame, text="搜索", width=80, command=self._search)
        self.search_btn.pack(side="right")

        # Search result info
        self.result_info = ctk.CTkLabel(
            self.parent, text="", anchor="w",
            font=ctk.CTkFont(size=13),
        )
        self.result_info.pack(fill="x", padx=10, pady=(5, 0))

        # Version selector
        ver_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        ver_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(ver_frame, text="版本:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.version_var = ctk.StringVar(value="最新")
        self.version_menu = ctk.CTkOptionMenu(ver_frame, variable=self.version_var, values=["最新"])
        self.version_menu.pack(side="left", padx=5)

        # Download buttons
        btn_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.dl_deps_btn = ctk.CTkButton(
            btn_frame, text="下载包及所有依赖", width=160,
            command=lambda: self._start_download(with_deps=True),
        )
        self.dl_deps_btn.pack(side="left", padx=3)

        self.dl_only_btn = ctk.CTkButton(
            btn_frame, text="仅下载包本身", width=120,
            command=lambda: self._start_download(with_deps=False),
        )
        self.dl_only_btn.pack(side="left", padx=3)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self.parent)
        self.progress.pack(fill="x", padx=10, pady=(5, 0))
        self.progress.set(0)

        # Log area
        log_label = ctk.CTkLabel(self.parent, text="下载日志:", anchor="w", font=ctk.CTkFont(size=12))
        log_label.pack(fill="x", padx=10, pady=(10, 0))

        self.log_text = ctk.CTkTextbox(self.parent, height=200, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _browse_dir(self):
        """Browse for store directory."""
        from tkinter import filedialog
        d = filedialog.askdirectory(title="选择包存储目录")
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)
            self.app.store_dir = d

    def _search(self):
        """Search PyPI for a package with mirror source failover."""
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_btn.configure(state="disabled", text="搜索中...")
        self.result_info.configure(text="正在搜索...")
        self.parent.update()

        def do_search():
            # Build JSON API URLs from enabled sources
            # e.g. https://pypi.tuna.tsinghua.edu.cn/simple → https://pypi.tuna.tsinghua.edu.cn/pypi/{name}/json
            sources = self.app.source_manager.get_enabled()

            for idx, src in enumerate(sources):
                base = src["url"].rstrip("/").replace("/simple", "")
                url = f"{base}/pypi/{query}/json"
                src_name = src["name"]

                try:
                    req = urllib.request.Request(url)
                    req.add_header("User-Agent", "OfflinePipManager/1.0")
                    req.add_header("Accept", "application/json")
                    # Short timeout per source for snappy feel, pypi.org gets longer
                    timeout = 5 if "pypi.org" not in url else 10
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        data = json.loads(resp.read().decode("utf-8"))

                    info = data.get("info", {})
                    name = info.get("name", query)
                    summary = info.get("summary", "")
                    version = info.get("version", "0.0.0")
                    versions = list(data.get("releases", {}).keys())

                    # Filter to non-prerelease, sort by version
                    from packaging.version import parse as parse_version
                    parsed_versions = []
                    for v in versions:
                        try:
                            pv = parse_version(v)
                            if not pv.is_prerelease:
                                parsed_versions.append((pv, v))
                        except Exception:
                            pass
                    parsed_versions.sort(key=lambda x: x[0], reverse=True)
                    sorted_versions = [v for _, v in parsed_versions]

                    self.result = {
                        "name": name,
                        "summary": summary,
                        "versions": sorted_versions if sorted_versions else [version],
                    }
                    self.parent.after(0, self._on_search_success)
                    self.parent.after(0, lambda s=src_name: self.app.set_status(f"搜索完成 (源: {s})"))
                    return

                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        self.parent.after(0, lambda: self._on_search_error("未找到该包，请检查包名是否正确。"))
                        return
                    # Other HTTP errors: try next source
                    continue
                except Exception:
                    # Network error / timeout: try next source
                    continue

            # All sources failed
            self.parent.after(0, lambda: self._on_search_error("搜索失败: 所有镜像源均无法访问。请检查网络或源配置。"))

        threading.Thread(target=do_search, daemon=True).start()

    def _on_search_success(self):
        """Handle successful search on UI thread."""
        r = self.result
        self.search_btn.configure(state="normal", text="搜索")
        self.result_info.configure(text=f"✓ {r['name']} — {r['summary'][:80]}")
        self.version_menu.configure(values=r["versions"])
        self.version_var.set(r["versions"][0] if r["versions"] else "最新")
        self.app.set_status(f"找到包: {r['name']}")

    def _on_search_error(self, msg: str):
        """Handle search error on UI thread."""
        self.search_btn.configure(state="normal", text="搜索")
        self.result_info.configure(text=f"✗ {msg}")
        self.app.set_status(msg)

    def _start_download(self, with_deps: bool):
        """Start downloading in a background thread."""
        if self._downloading:
            return

        pkg_name = self.result.get("name") if hasattr(self, "result") else self.search_entry.get().strip()
        if not pkg_name:
            messagebox.showwarning("提示", "请先搜索一个包。")
            return

        version = self.version_var.get()
        if version == "最新":
            version = None

        store_dir = self.dir_entry.get().strip()
        self.app.store_dir = store_dir

        self._downloading = True
        self.dl_deps_btn.configure(state="disabled")
        self.dl_only_btn.configure(state="disabled")
        self.log_text.delete("1.0", "end")
        self.progress.set(0)

        self.app.set_status(f"正在下载 {pkg_name}...")

        def do_download():
            downloader = Downloader(self.app.source_manager, store_dir)
            success = downloader.download(
                pkg_name,
                version=version,
                with_deps=with_deps,
                on_progress=lambda p: self.parent.after(0, lambda: self.progress.set(p / 100.0)),
                on_log=lambda line: self.parent.after(0, lambda l=line: self._append_log(l)),
            )
            self.parent.after(0, lambda s=success: self._on_download_done(s))

        threading.Thread(target=do_download, daemon=True).start()

    def _append_log(self, line: str):
        """Append a line to the log textbox."""
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")

    def _on_download_done(self, success: bool):
        """Handle download completion on UI thread."""
        self._downloading = False
        self.dl_deps_btn.configure(state="normal")
        self.dl_only_btn.configure(state="normal")

        if success:
            self.app.set_status("下载完成")
            messagebox.showinfo("完成", "包下载成功！")
        else:
            self.app.set_status("下载失败")
