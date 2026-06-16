"""Source management tab — view, add, remove, reorder mirror sources."""

import customtkinter as ctk
from tkinter import messagebox


class SourceTab:
    """Tab for managing pip mirror sources."""

    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.source_manager = app.source_manager
        self._source_frames: list = []
        self._selected_index: int | None = None
        self._radio_var = ctk.IntVar(value=-1)
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        """Build the source management UI."""
        # Header
        header = ctk.CTkLabel(
            self.parent, text="镜像源管理",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(pady=(10, 5), anchor="w")

        desc = ctk.CTkLabel(
            self.parent,
            text="管理 pip 镜像源列表。点击选中一行后用下方按钮操作。排在上面的优先使用。",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        desc.pack(pady=(0, 10), anchor="w")

        # Scrollable frame for source list
        self.list_frame = ctk.CTkScrollableFrame(self.parent)
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Button bar
        btn_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.add_btn = ctk.CTkButton(
            btn_frame, text="添加", width=80,
            command=self._add_source,
        )
        self.add_btn.pack(side="left", padx=3)

        self.del_btn = ctk.CTkButton(
            btn_frame, text="删除", width=80,
            command=self._remove_source,
            fg_color="#c0392b", hover_color="#e74c3c",
        )
        self.del_btn.pack(side="left", padx=3)

        self.up_btn = ctk.CTkButton(
            btn_frame, text="↑ 上移", width=80,
            command=self._move_up,
        )
        self.up_btn.pack(side="left", padx=3)

        self.down_btn = ctk.CTkButton(
            btn_frame, text="↓ 下移", width=80,
            command=self._move_down,
        )
        self.down_btn.pack(side="left", padx=3)

        self.test_btn = ctk.CTkButton(
            btn_frame, text="测试连接", width=100,
            command=self._test_connection,
        )
        self.test_btn.pack(side="right", padx=3)

        # Column headers hint
        hint_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
        hint_frame.pack(fill="x", padx=5, pady=(5, 0))
        ctk.CTkLabel(hint_frame, text="", width=30).pack(side="left")  # radio spacer
        ctk.CTkLabel(hint_frame, text="序号", width=40, font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        ctk.CTkLabel(hint_frame, text="启用", width=40, font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        ctk.CTkLabel(hint_frame, text="源名称", width=80, font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        ctk.CTkLabel(hint_frame, text="URL", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left", fill="x", expand=True)

    def _refresh_list(self):
        """Rebuild the source list from the source manager."""
        for frame in self._source_frames:
            frame.destroy()
        self._source_frames.clear()

        sources = self.source_manager.load()
        self._radio_var = ctk.IntVar(value=self._selected_index if self._selected_index is not None and self._selected_index < len(sources) else -1)

        for idx, src in enumerate(sources):
            self._add_source_row(idx, src)

    def _add_source_row(self, idx: int, src: dict):
        """Add a single source row to the list."""
        is_selected = (idx == self._selected_index)
        bg = self._get_row_color(is_selected)

        frame = ctk.CTkFrame(self.list_frame, fg_color=bg)
        frame.pack(fill="x", padx=5, pady=2)

        # Click on frame to select
        for widget in (frame,):
            widget.bind("<Button-1>", lambda e, i=idx: self._select_row(i))

        # Radio button for selection
        rb = ctk.CTkRadioButton(
            frame, text="", width=20, variable=self._radio_var, value=idx,
            command=lambda i=idx: self._select_row(i),
        )
        rb.pack(side="left", padx=(5, 5))

        # Index
        idx_label = ctk.CTkLabel(frame, text=str(idx + 1), width=35, font=ctk.CTkFont(size=13))
        idx_label.pack(side="left", padx=(0, 5))
        idx_label.bind("<Button-1>", lambda e, i=idx: self._select_row(i))

        # Enabled checkbox
        var = ctk.BooleanVar(value=src.get("enabled", True))
        cb = ctk.CTkCheckBox(
            frame, text="", width=30, variable=var,
            command=lambda i=idx, v=var: self._on_toggle(i, v.get()),
        )
        cb.pack(side="left", padx=(0, 5))

        # Name
        name_label = ctk.CTkLabel(frame, text=src["name"], width=80, anchor="w", font=ctk.CTkFont(size=13))
        name_label.pack(side="left")
        name_label.bind("<Button-1>", lambda e, i=idx: self._select_row(i))

        # URL
        url_label = ctk.CTkLabel(
            frame, text=src["url"], anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="gray" if not is_selected else "white",
        )
        url_label.pack(side="left", fill="x", expand=True, padx=10)
        url_label.bind("<Button-1>", lambda e, i=idx: self._select_row(i))

        self._source_frames.append(frame)

    def _get_row_color(self, selected: bool) -> str:
        """Get background color for a row based on selection state."""
        if selected:
            return "#1f538d"  # highlighted blue
        return "transparent"

    def _select_row(self, index: int):
        """Select a row by index."""
        self._selected_index = index
        self._radio_var.set(index)
        self._refresh_list()
        src = self.source_manager.load()[index]
        self.app.set_status(f"已选中: {src['name']}")

    def _get_selected_or_warn(self) -> int | None:
        """Return the selected index, or show warning if nothing selected."""
        if self._selected_index is None or self._selected_index < 0:
            messagebox.showinfo("提示", "请先在列表中选择一个镜像源（点击行或单选按钮）。")
            return None
        sources = self.source_manager.load()
        if self._selected_index >= len(sources):
            self._selected_index = None
            return None
        return self._selected_index

    def _on_toggle(self, index: int, enabled: bool):
        """Handle enable/disable toggle."""
        sources = self.source_manager.load()
        if 0 <= index < len(sources):
            if sources[index].get("enabled") != enabled:
                self.source_manager.toggle(index)
                self.app.set_status(f"源 '{sources[index]['name']}' {'启用' if enabled else '禁用'}")

    def _add_source(self):
        """Show dialog to add a new source."""
        dialog = ctk.CTkInputDialog(
            text="请输入镜像源名称:",
            title="添加镜像源",
        )
        name = dialog.get_input()
        if not name:
            return

        dialog2 = ctk.CTkInputDialog(
            text=f"请输入 '{name}' 的 URL (以 /simple 结尾):",
            title="添加镜像源",
        )
        url = dialog2.get_input()
        if not url:
            return

        self.source_manager.add(name, url)
        self._selected_index = None
        self._refresh_list()
        self.app.set_status(f"已添加源: {name}")

    def _remove_source(self):
        """Remove the selected source."""
        idx = self._get_selected_or_warn()
        if idx is None:
            return

        sources = self.source_manager.load()
        src = sources[idx]
        ok = messagebox.askyesno("确认删除", f"确定要删除镜像源 '{src['name']}' 吗？")
        if ok:
            self.source_manager.remove(idx)
            self._selected_index = None
            self._refresh_list()
            self.app.set_status(f"已删除源: {src['name']}")

    def _move_up(self):
        """Move selected source up in priority."""
        idx = self._get_selected_or_warn()
        if idx is None:
            return
        if idx == 0:
            messagebox.showinfo("提示", "已经是第一位，无法上移。")
            return

        self.source_manager.move_up(idx)
        self._selected_index = idx - 1
        self._refresh_list()
        self.app.set_status("已上移")

    def _move_down(self):
        """Move selected source down in priority."""
        idx = self._get_selected_or_warn()
        if idx is None:
            return

        sources = self.source_manager.load()
        if idx >= len(sources) - 1:
            messagebox.showinfo("提示", "已经是最后一位，无法下移。")
            return

        self.source_manager.move_down(idx)
        self._selected_index = idx + 1
        self._refresh_list()
        self.app.set_status("已下移")

    def _test_connection(self):
        """Test connection to the selected source (runs in background thread)."""
        idx = self._get_selected_or_warn()
        if idx is None:
            return

        sources = self.source_manager.load()
        src = sources[idx]
        self.app.set_status(f"正在测试 {src['name']} ...")
        self.test_btn.configure(state="disabled", text="测试中...")

        import threading

        def do_test():
            ok, msg = self.source_manager.test_connection(src["url"])
            self.parent.after(0, lambda: self._on_test_done(ok, msg, src["name"]))

        threading.Thread(target=do_test, daemon=True).start()

    def _on_test_done(self, ok: bool, msg: str, name: str):
        """Handle test connection result on UI thread."""
        self.test_btn.configure(state="normal", text="测试连接")

        if ok:
            messagebox.showinfo("测试结果", f"✓ {name}\n{msg}")
        else:
            messagebox.showwarning("测试结果", f"✗ {name}\n{msg}")

        self.app.set_status(f"测试完成: {name} - {msg}")
