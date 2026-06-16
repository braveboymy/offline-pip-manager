"""Offline install tab — install packages from local store to target environment."""

import threading

import customtkinter as ctk
from tkinter import messagebox

from core.package_index import scan_directory
from core.installer import Installer


class InstallTab:
    """Tab for installing packages offline from local store."""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self._packages: list[dict] = []
        self._checkboxes: dict = {}
        self._row_frames: list = []
        self._installing = False

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        """Build the offline install UI."""
        # Header
        header = ctk.CTkLabel(
            self.parent, text="离线安装",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(pady=(10, 5), anchor="w")

        desc = ctk.CTkLabel(
            self.parent,
            text="从本地包目录安装到目标 Python 环境。适用于无法联网的电脑。",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(pady=(0, 10), anchor="w")

        # Store directory
        dir_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        dir_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(dir_frame, text="包目录:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.dir_entry = ctk.CTkEntry(dir_frame)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.dir_entry.insert(0, self.app.store_dir)
        ctk.CTkButton(dir_frame, text="浏览", width=60, command=self._browse_dir).pack(side="right")

        # Python path
        py_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        py_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(py_frame, text="Python:", font=ctk.CTkFont(size=13)).pack(side="left")
        self.py_entry = ctk.CTkEntry(py_frame)
        self.py_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.py_entry.insert(0, "python")
        ctk.CTkButton(py_frame, text="浏览", width=60, command=self._browse_python).pack(side="right")

        # Column headers
        col_frame = ctk.CTkFrame(self.parent)
        col_frame.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(col_frame, text="选择", width=50, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(5, 0))
        ctk.CTkLabel(col_frame, text="包名", width=200, font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        ctk.CTkLabel(col_frame, text="版本", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

        # Scrollable package list
        self.list_frame = ctk.CTkScrollableFrame(self.parent)
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Button bar
        btn_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="全选", width=60, command=self._select_all).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="取消全选", width=70, command=self._deselect_all).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="刷新列表", width=80,
            command=self._refresh, fg_color="#555",
        ).pack(side="left", padx=3)

        self.install_btn = ctk.CTkButton(
            btn_frame, text="安装选中的包", width=140,
            command=self._install,
            fg_color="#2980b9", hover_color="#3498db",
        )
        self.install_btn.pack(side="right", padx=3)

        # Log area
        log_label = ctk.CTkLabel(self.parent, text="安装日志:", anchor="w", font=ctk.CTkFont(size=12))
        log_label.pack(fill="x", padx=10, pady=(10, 0))

        self.log_text = ctk.CTkTextbox(self.parent, height=180, font=ctk.CTkFont(size=11))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _browse_dir(self):
        """Browse for store directory."""
        from tkinter import filedialog
        d = filedialog.askdirectory(title="选择包存储目录")
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)
            self._refresh()

    def _browse_python(self):
        """Browse for python executable."""
        from tkinter import filedialog
        f = filedialog.askopenfilename(
            title="选择 python.exe",
            filetypes=[("Python", "python.exe"), ("All Files", "*.*")],
        )
        if f:
            self.py_entry.delete(0, "end")
            self.py_entry.insert(0, f)

    def _refresh(self):
        """Refresh the package list."""
        store_dir = self.dir_entry.get().strip()

        # Clear existing
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames.clear()
        self._checkboxes.clear()

        try:
            self._packages = scan_directory(store_dir)
        except FileNotFoundError:
            self._packages = []
            return

        for pkg in self._packages:
            self._add_row(pkg)

        self.app.set_status(f"加载了 {len(self._packages)} 个可安装包")

    def _add_row(self, pkg: dict):
        """Add a package row to the checklist."""
        frame = ctk.CTkFrame(self.list_frame)
        frame.pack(fill="x", pady=1)

        var = ctk.BooleanVar(value=False)
        cb = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
        cb.pack(side="left", padx=(8, 0))
        self._checkboxes[pkg["name"]] = (var, pkg)

        ctk.CTkLabel(frame, text=pkg["name"], width=200, anchor="w").pack(side="left")
        ctk.CTkLabel(frame, text=pkg["version"], anchor="w").pack(side="left")

        self._row_frames.append(frame)

    def _select_all(self):
        """Select all packages."""
        for var, _ in self._checkboxes.values():
            var.set(True)

    def _deselect_all(self):
        """Deselect all packages."""
        for var, _ in self._checkboxes.values():
            var.set(False)

    def _install(self):
        """Install selected packages."""
        if self._installing:
            return

        selected = [name for name, (var, _) in self._checkboxes.items() if var.get()]
        if not selected:
            messagebox.showinfo("提示", "请先选择要安装的包。")
            return

        store_dir = self.dir_entry.get().strip()
        python_path = self.py_entry.get().strip()

        ok = messagebox.askyesno(
            "确认安装",
            f"将使用 Python ({python_path}) 安装以下 {len(selected)} 个包:\n\n" +
            "\n".join(selected[:15]) +
            ("\n..." if len(selected) > 15 else "") +
            f"\n\n离线源目录: {store_dir}\n\n继续？"
        )
        if not ok:
            return

        self._installing = True
        self.install_btn.configure(state="disabled", text="安装中...")
        self.log_text.delete("1.0", "end")
        self.app.set_status(f"正在安装 {len(selected)} 个包...")

        def do_install():
            installer = Installer(store_dir, python_path=python_path)
            success = installer.install(
                selected,
                on_log=lambda line: self.parent.after(0, lambda l=line: self._append_log(l)),
            )
            self.parent.after(0, lambda s=success: self._on_install_done(s))

        threading.Thread(target=do_install, daemon=True).start()

    def _append_log(self, line: str):
        """Append a line to the log textbox."""
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")

    def _on_install_done(self, success: bool):
        """Handle install completion on UI thread."""
        self._installing = False
        self.install_btn.configure(state="normal", text="安装选中的包")

        if success:
            self.app.set_status("安装完成")
            messagebox.showinfo("完成", "包安装成功！")
        else:
            self.app.set_status("安装失败，请查看日志")
