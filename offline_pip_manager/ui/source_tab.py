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
            text="管理 pip 镜像源列表。拖动或使用按钮调整优先级，排在上面的优先使用。",
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
        ctk.CTkLabel(hint_frame, text="序号 源名称", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        ctk.CTkLabel(hint_frame, text="URL", font=ctk.CTkFont(size=11), text_color="gray").pack(side="right")

    def _refresh_list(self):
        """Rebuild the source list from the source manager."""
        # Clear existing
        for frame in self._source_frames:
            frame.destroy()
        self._source_frames.clear()

        sources = self.source_manager.load()
        for idx, src in enumerate(sources):
            self._add_source_row(idx, src)

    def _add_source_row(self, idx: int, src: dict):
        """Add a single source row to the list."""
        frame = ctk.CTkFrame(self.list_frame)
        frame.pack(fill="x", padx=5, pady=2)

        # Index
        idx_label = ctk.CTkLabel(frame, text=str(idx + 1), width=35, font=ctk.CTkFont(size=13))
        idx_label.pack(side="left", padx=(5, 0))

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

        # URL
        url_label = ctk.CTkLabel(
            frame, text=src["url"], anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        url_label.pack(side="left", fill="x", expand=True, padx=10)

        self._source_frames.append(frame)

    def _on_toggle(self, index: int, enabled: bool):
        """Handle enable/disable toggle."""
        # The toggle checkbox already set the new value, we just need to sync
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
        self._refresh_list()
        self.app.set_status(f"已添加源: {name}")

    def _remove_source(self):
        """Remove the last selected source."""
        sources = self.source_manager.load()
        if not sources:
            return

        # Remove the last one (simple approach - user can use buttons to reorder)
        last = sources[-1]
        ok = messagebox.askyesno("确认删除", f"确定要删除镜像源 '{last['name']}' 吗？")
        if ok:
            self.source_manager.remove(len(sources) - 1)
            self._refresh_list()
            self.app.set_status(f"已删除源: {last['name']}")

    def _move_up(self):
        """Move a source up in priority. Find first non-first enabled source."""
        sources = self.source_manager.load()
        # Find the last selected / prominent source to move
        # For simplicity, move the last element up
        if len(sources) > 1:
            self.source_manager.move_up(len(sources) - 1)
            self._refresh_list()
            self.app.set_status("已上移")

    def _move_down(self):
        """Move a source down in priority."""
        sources = self.source_manager.load()
        if len(sources) > 1:
            self.source_manager.move_down(len(sources) - 2)
            self._refresh_list()
            self.app.set_status("已下移")

    def _test_connection(self):
        """Test connection to the last source."""
        sources = self.source_manager.load()
        if not sources:
            messagebox.showinfo("提示", "没有可测试的镜像源。")
            return

        # Test the last source
        src = sources[-1]
        self.app.set_status(f"正在测试 {src['name']} ...")
        self.test_btn.configure(state="disabled", text="测试中...")
        self.parent.update()

        ok, msg = self.source_manager.test_connection(src["url"])
        self.test_btn.configure(state="normal", text="测试连接")

        if ok:
            messagebox.showinfo("测试结果", f"✓ {src['name']}\n{msg}")
        else:
            messagebox.showwarning("测试结果", f"✗ {src['name']}\n{msg}")

        self.app.set_status(f"测试完成: {src['name']} - {msg}")
