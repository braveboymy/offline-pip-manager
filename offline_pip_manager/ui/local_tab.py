"""Local package management tab — view, check updates, delete local packages."""

import os
import threading

import customtkinter as ctk
from tkinter import messagebox

from core.package_index import scan_directory
from core.checker import VersionChecker


class LocalTab:
    """Tab for managing locally downloaded packages."""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._packages: list[dict] = []
        self._checkboxes: dict = {}
        self._row_frames: list = []
        self._updating = False

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        """Build the local package management UI."""
        # Header
        header = ctk.CTkLabel(
            self.parent, text="本地包管理",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(pady=(10, 5), anchor="w")

        desc = ctk.CTkLabel(
            self.parent,
            text="管理已下载到本地的 Python 包文件。可以检查更新或删除旧版本。",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(pady=(0, 10), anchor="w")

        # Directory selector
        dir_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        dir_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(dir_frame, text="存储目录:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.dir_entry = ctk.CTkEntry(dir_frame)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.dir_entry.insert(0, self.app.store_dir)
        ctk.CTkButton(dir_frame, text="浏览", width=60, command=self._browse_dir).pack(side="right")

        # Column headers
        col_frame = ctk.CTkFrame(self.parent)
        col_frame.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(col_frame, text="选择", width=40, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(5, 0))
        ctk.CTkLabel(col_frame, text="包名", width=150, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(col_frame, text="版本", width=100, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(col_frame, text="大小", width=80, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(col_frame, text="日期", width=140, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        status_label = ctk.CTkLabel(col_frame, text="状态", font=ctk.CTkFont(size=11, weight="bold"))
        status_label.pack(side="left", padx=10)

        # Scrollable package list
        self.list_frame = ctk.CTkScrollableFrame(self.parent)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Button bar
        btn_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="全选", width=60, command=self._select_all).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="取消全选", width=70, command=self._deselect_all).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="刷新", width=60,
            command=self._refresh, fg_color="#555",
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="检查更新", width=100,
            command=self._check_updates,
        ).pack(side="left", padx=20)
        ctk.CTkButton(
            btn_frame, text="删除选中", width=100,
            command=self._delete_selected,
            fg_color="#c0392b", hover_color="#e74c3c",
        ).pack(side="right", padx=3)

        # Status summary
        self.summary_label = ctk.CTkLabel(
            self.parent, text="", anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self.summary_label.pack(fill="x", padx=10, pady=(0, 5))

    def _browse_dir(self):
        """Browse for store directory."""
        from tkinter import filedialog
        d = filedialog.askdirectory(title="选择包存储目录")
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)
            self.app.store_dir = d
            self._refresh()

    def _refresh(self):
        """Refresh the package list from the store directory."""
        store_dir = self.dir_entry.get().strip()
        self.app.store_dir = store_dir

        # Clear existing
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames.clear()
        self._checkboxes.clear()

        try:
            self._packages = scan_directory(store_dir)
        except FileNotFoundError:
            self._packages = []
            self.summary_label.configure(text="目录不存在，请检查路径。")
            return

        if not self._packages:
            self.summary_label.configure(text="暂无包文件。使用「下载」标签页添加包。")
            return

        for pkg in self._packages:
            self._add_row(pkg)

        total_size = sum(p["size"] for p in self._packages)
        size_str = self._format_size(total_size)
        self.summary_label.configure(text=f"共 {len(self._packages)} 个包，总大小: {size_str}")
        self.app.set_status(f"加载了 {len(self._packages)} 个本地包")

    def _format_size(self, size: int) -> str:
        """Format bytes to human readable."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _add_row(self, pkg: dict):
        """Add a package row to the list."""
        frame = ctk.CTkFrame(self.list_frame)
        frame.pack(fill="x", pady=1)

        # Checkbox
        var = ctk.BooleanVar(value=False)
        cb = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
        cb.pack(side="left", padx=(5, 0))
        self._checkboxes[pkg["name"]] = (var, pkg)

        # Name
        ctk.CTkLabel(frame, text=pkg["name"], width=150, anchor="w").pack(side="left")

        # Version
        ctk.CTkLabel(frame, text=pkg["version"], width=100, anchor="w").pack(side="left")

        # Size
        ctk.CTkLabel(frame, text=self._format_size(pkg["size"]), width=80, anchor="w").pack(side="left")

        # Date
        ctk.CTkLabel(frame, text=pkg["date"], width=140, anchor="w").pack(side="left")

        # Status
        status_label = ctk.CTkLabel(frame, text="— 未检查", anchor="w", text_color="gray")
        status_label.pack(side="left", padx=10)
        # Store reference for update
        pkg["_status_label"] = status_label

        self._row_frames.append(frame)

    def _select_all(self):
        """Select all packages."""
        for var, _ in self._checkboxes.values():
            var.set(True)

    def _deselect_all(self):
        """Deselect all packages."""
        for var, _ in self._checkboxes.values():
            var.set(False)

    def _check_updates(self):
        """Check for updates for all local packages."""
        if self._updating or not self._packages:
            if not self._packages:
                messagebox.showinfo("提示", "没有可检查的包。")
            return

        self._updating = True
        self.app.set_status("正在检查更新...")

        # Reset status
        for pkg in self._packages:
            if "_status_label" in pkg:
                pkg["_status_label"].configure(text="检查中...", text_color="gray")

        def do_check():
            checker = VersionChecker(self.app.source_manager)
            results = checker.check_all(self._packages)

            def update_ui():
                self._updating = False
                update_count = 0
                fetch_fail = 0
                for r in results:
                    for pkg in self._packages:
                        if pkg["name"] == r["name"]:
                            label = pkg.get("_status_label")
                            if not label:
                                continue
                            if r["latest"] == "(检查失败)":
                                label.configure(text="⚠ 检查失败", text_color="orange")
                                fetch_fail += 1
                            elif r["has_update"]:
                                label.configure(
                                    text=f"▲ 有更新: {r['latest']}",
                                    text_color="#e67e22",
                                )
                                update_count += 1
                            else:
                                label.configure(text="● 已是最新", text_color="#27ae60")
                            break

                status = f"检查完成: {len(results)} 个包"
                if update_count > 0:
                    status += f", {update_count} 个有更新"
                if fetch_fail > 0:
                    status += f", {fetch_fail} 个检查失败"
                self.app.set_status(status)

            self.parent.after(0, update_ui)

        threading.Thread(target=do_check, daemon=True).start()

    def _delete_selected(self):
        """Delete selected packages."""
        selected = [(name, pkg) for name, (var, pkg) in self._checkboxes.items() if var.get()]

        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的包。")
            return

        names = [name for name, _ in selected]
        ok = messagebox.askyesno(
            "确认删除",
            f"确定要删除以下 {len(names)} 个包吗？\n\n" + "\n".join(names[:10]) +
            ("\n..." if len(names) > 10 else "")
        )
        if not ok:
            return

        deleted = 0
        for name, pkg in selected:
            try:
                os.remove(pkg["path"])
                deleted += 1
            except OSError as e:
                messagebox.showwarning("删除失败", f"无法删除 {name}: {e}")

        self.app.set_status(f"已删除 {deleted} 个包")
        self._refresh()
