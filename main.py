#!/usr/bin/env python3
"""
Frame2File - Image to PDF GUI
Double-click this file to open a small window.
"""

from __future__ import annotations

import re
import sys
import threading
import ctypes
from pathlib import Path
from typing import Callable, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageFile, ImageTk
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Pillow belum terpasang",
        "Install Pillow dulu lewat PowerShell:\n\npy -m pip install pillow"
    )
    raise SystemExit(1)

ImageFile.LOAD_TRUNCATED_IMAGES = True

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
THUMBNAIL_FILTER = getattr(Image, "Resampling", Image).LANCZOS


def enable_dark_title_bar(root: tk.Tk) -> None:
    if sys.platform != "win32":
        return

    try:
        root.update_idletasks()
        hwnd = root.winfo_id()
        enabled = ctypes.c_int(1)
        caption_color = ctypes.c_int(0x000000)
        text_color = ctypes.c_int(0xFFFFFF)

        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(enabled),
                ctypes.sizeof(enabled),
            )
            if result == 0:
                break

        for attribute, color in ((35, caption_color), (36, text_color)):
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                attribute,
                ctypes.byref(color),
                ctypes.sizeof(color),
            )
    except Exception:
        pass


def natural_key(path: Path) -> list:
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def find_images(folder: Path) -> List[Path]:
    return sorted(
        [
            file for file in folder.iterdir()
            if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=natural_key,
    )


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[index:index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def blend_colors(base: str, overlay: str, amount: float) -> str:
    base_rgb = hex_to_rgb(base)
    overlay_rgb = hex_to_rgb(overlay)
    return rgb_to_hex(
        tuple(
            round(base_rgb[index] + (overlay_rgb[index] - base_rgb[index]) * amount)
            for index in range(3)
        )
    )


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    radius: int,
    **kwargs,
) -> int:
    radius = min(radius, max(0, (x2 - x1) // 2), max(0, (y2 - y1) // 2))
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=18, **kwargs)


class RoundedFrame(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        bg: str,
        fill: str,
        radius: int = 18,
        padding: int | tuple[int, int] = 16,
        outline: str = "",
        shadow: str = "",
        shadow_offset: int = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        super().__init__(parent, bg=bg, bd=0, highlightthickness=0)
        self.bg_color = bg
        self.fill = fill
        self.radius = radius
        self.outline = outline
        self.shadow = shadow
        self.shadow_offset = shadow_offset
        if width is not None:
            self.configure(width=width)
        if height is not None:
            self.configure(height=height)
        if width is not None or height is not None:
            self.pack_propagate(False)

        if isinstance(padding, tuple):
            self.pad_x, self.pad_y = padding
        else:
            self.pad_x = self.pad_y = padding

        self.canvas = tk.Canvas(
            self,
            bg=bg,
            width=width or 1,
            height=height or 1,
            bd=0,
            highlightthickness=0,
            relief="flat",
        )
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=fill, bd=0, highlightthickness=0)
        self.window_id = self.canvas.create_window(
            self.pad_x,
            self.pad_y,
            window=self.inner,
            anchor="nw",
        )
        self.canvas.bind("<Configure>", self.redraw)

    def redraw(self, event: tk.Event) -> None:
        self.canvas.delete("shape")
        width = max(event.width, 1)
        height = max(event.height, 1)

        if self.shadow and self.shadow_offset:
            draw_rounded_rect(
                self.canvas,
                self.shadow_offset,
                self.shadow_offset + 2,
                width - self.shadow_offset,
                height - self.shadow_offset,
                self.radius,
                fill=self.shadow,
                outline="",
                tags="shape",
            )

        draw_rounded_rect(
            self.canvas,
            1,
            1,
            width - self.shadow_offset - 2,
            height - self.shadow_offset - 3,
            self.radius,
            fill=self.fill,
            outline=self.outline,
            width=1 if self.outline else 0,
            tags="shape",
        )
        self.canvas.tag_lower("shape")
        self.canvas.itemconfigure(
            self.window_id,
            width=max(width - self.pad_x * 2 - self.shadow_offset, 1),
            height=max(height - self.pad_y * 2 - self.shadow_offset, 1),
        )

    def set_style(self, fill: Optional[str] = None, outline: Optional[str] = None, shadow: Optional[str] = None) -> None:
        if fill is not None:
            self.fill = fill
            self.inner.configure(bg=fill)
        if outline is not None:
            self.outline = outline
        if shadow is not None:
            self.shadow = shadow
        event = tk.Event()
        event.width = self.winfo_width()
        event.height = self.winfo_height()
        self.redraw(event)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg: str,
        fg: str,
        hover_bg: str,
        active_bg: str,
        radius: int = 12,
        height: int = 38,
        font: tuple[str, int, str] = ("Segoe UI", 9, "bold"),
        padx: int = 18,
        width: Optional[int] = None,
    ) -> None:
        super().__init__(
            parent,
            width=width or max(96, len(text) * 10 + padx * 2),
            height=height,
            bg=parent.cget("bg"),
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.active_bg = active_bg
        self.fg = fg
        self.radius = radius
        self.button_height = height
        self.font = font
        self.padx = padx
        self.state = "normal"
        self.current_bg = bg

        self.bind("<Configure>", lambda _event: self.draw())
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        state = kwargs.pop("state", None)
        if state is not None:
            self.state = state
            self.current_bg = blend_colors(self.normal_bg, "#000000", 0.28) if state == "disabled" else self.normal_bg
            self.itemconfigure("label", fill=blend_colors(self.fg, "#000000", 0.32) if state == "disabled" else self.fg)
            super().configure(cursor="arrow" if state == "disabled" else "hand2")
            self.draw()
        return super().configure(cnf, **kwargs)

    config = configure

    def draw(self) -> None:
        self.delete("all")
        width = max(self.winfo_width(), self.padx * 2 + 90)
        height = self.button_height
        draw_rounded_rect(
            self,
            0,
            0,
            width - 1,
            height - 1,
            self.radius,
            fill=self.current_bg,
            outline="",
        )
        self.create_text(
            width // 2,
            height // 2,
            text=self.text,
            fill=self.fg if self.state != "disabled" else blend_colors(self.fg, "#000000", 0.32),
            font=self.font,
            tags="label",
        )

    def on_enter(self, _event: tk.Event) -> None:
        if self.state == "disabled":
            return
        self.current_bg = self.hover_bg
        self.draw()

    def on_leave(self, _event: tk.Event) -> None:
        if self.state == "disabled":
            return
        self.current_bg = self.normal_bg
        self.draw()

    def on_press(self, _event: tk.Event) -> None:
        if self.state == "disabled":
            return
        self.current_bg = self.active_bg
        self.draw()

    def on_release(self, event: tk.Event) -> None:
        if self.state == "disabled":
            return

        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        self.current_bg = self.hover_bg if inside else self.normal_bg
        self.draw()
        if inside:
            self.command()


class Frame2FileApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Frame2File")
        self.root.geometry("1180x980")
        self.root.minsize(900, 840)
        self.root.resizable(True, True)
        
        # Dark theme colors
        self.BG_PRIMARY = "#080d14"
        self.BG_SECONDARY = "#111924"
        self.BG_TERTIARY = "#1a2532"
        self.SURFACE_ELEVATED = "#15202c"
        self.SURFACE_SOFT = "#1d2a38"
        self.BORDER_SUBTLE = "#263445"
        self.ACCENT_PRIMARY = "#5ea8ff"
        self.ACCENT_SECONDARY = "#8ec5ff"
        self.ACCENT_HOVER = "#77b7ff"
        self.TEXT_PRIMARY = "#eef5ff"
        self.TEXT_SECONDARY = "#a9b8c9"
        self.TEXT_MUTED = "#738397"
        self.SUCCESS = "#31c968"
        self.SUCCESS_HOVER = "#48dd7b"
        self.SUCCESS_ACTIVE = "#24a956"
        self.DANGER = "#e65b66"
        self.DANGER_HOVER = "#f0717c"
        self.DANGER_ACTIVE = "#c84b55"
        self.SHADOW = "#05080d"
        
        # Set window background
        self.root.configure(bg=self.BG_PRIMARY)
        enable_dark_title_bar(self.root)
        
        self.folder_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.status_text = tk.StringVar(value="📁 Pilih folder gambar untuk memulai")
        self.progress_value = tk.IntVar(value=0)
        self.image_paths: List[Path] = []
        self.selected_index: Optional[int] = None
        self.drag_start_index: Optional[int] = None
        self.thumbnail_refs: List[ImageTk.PhotoImage] = []
        self.preview_items: List[tk.Frame] = []
        self.drag_ghost: Optional[tk.Toplevel] = None
        self.drag_ghost_photo: Optional[ImageTk.PhotoImage] = None
        self.drop_insert_index: Optional[int] = None
        self.drop_indicator_widget: Optional[tk.Frame] = None
        self.flash_index: Optional[int] = None
        self.scroll_thumb_id: Optional[int] = None
        self.scrollbar_dragging = False
        self.scrollbar_first = 0.0
        self.scrollbar_last = 1.0
        self.action_buttons: List[RoundedButton] = []

        self._setup_styles()
        self._build_ui()
        self.render_preview()
        self.root.after(50, lambda: enable_dark_title_bar(self.root))
        self.root.after(250, lambda: enable_dark_title_bar(self.root))

    def _setup_styles(self) -> None:
        """Setup custom dark theme styles"""
        style = ttk.Style()
        
        # Configure Frame style
        style.configure(
            "Dark.TFrame",
            background=self.BG_PRIMARY,
            relief="flat",
            borderwidth=0
        )
        
        style.configure(
            "Card.TFrame",
            background=self.BG_SECONDARY,
            relief="flat",
            borderwidth=0
        )
        
        # Configure Label styles
        style.configure(
            "Dark.TLabel",
            background=self.BG_PRIMARY,
            foreground=self.TEXT_PRIMARY,
            font=("Segoe UI", 9)
        )
        
        style.configure(
            "Title.TLabel",
            background=self.BG_PRIMARY,
            foreground=self.ACCENT_PRIMARY,
            font=("Segoe UI", 24, "bold")
        )
        
        style.configure(
            "Subtitle.TLabel",
            background=self.BG_PRIMARY,
            foreground=self.TEXT_SECONDARY,
            font=("Segoe UI", 10)
        )
        
        style.configure(
            "CardLabel.TLabel",
            background=self.BG_SECONDARY,
            foreground=self.TEXT_SECONDARY,
            font=("Segoe UI", 8)
        )
        
        # Configure Entry style
        style.configure(
            "Dark.TEntry",
            background=self.BG_TERTIARY,
            foreground=self.TEXT_PRIMARY,
            fieldbackground=self.BG_TERTIARY,
            borderwidth=1,
            relief="solid",
            padding=5
        )
        
        # Configure Button styles
        style.configure(
            "Dark.TButton",
            background=self.BG_TERTIARY,
            foreground=self.TEXT_PRIMARY,
            borderwidth=1,
            relief="solid",
            padding=8,
            font=("Segoe UI", 9)
        )
        
        style.map(
            "Dark.TButton",
            background=[("active", self.ACCENT_HOVER), ("pressed", self.ACCENT_PRIMARY)],
            foreground=[("active", self.TEXT_PRIMARY)]
        )
        
        style.configure(
            "Primary.TButton",
            background=self.ACCENT_PRIMARY,
            foreground=self.BG_PRIMARY,
            borderwidth=0,
            relief="flat",
            padding=12,
            font=("Segoe UI", 10, "bold")
        )
        
        style.map(
            "Primary.TButton",
            background=[("active", self.ACCENT_HOVER), ("pressed", self.ACCENT_SECONDARY)],
            foreground=[("active", self.BG_PRIMARY)]
        )
        
        # Configure Progressbar style
        style.configure(
            "Dark.Horizontal.TProgressbar",
            background=self.SUCCESS,
            troughcolor=self.BG_TERTIARY,
            borderwidth=0,
            thickness=6
        )

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self.root, bg=self.BG_PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=34, pady=24)

        header_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        header_frame.pack(fill="x", pady=(0, 20))

        logo_canvas = tk.Canvas(
            header_frame,
            width=58,
            height=58,
            bg=self.BG_PRIMARY,
            bd=0,
            highlightthickness=0,
        )
        logo_canvas.pack(side="left", padx=(0, 16))
        draw_rounded_rect(
            logo_canvas,
            2,
            2,
            56,
            56,
            18,
            fill=self.SURFACE_ELEVATED,
            outline=self.BORDER_SUBTLE,
        )
        draw_rounded_rect(
            logo_canvas,
            10,
            10,
            48,
            48,
            14,
            fill=blend_colors(self.ACCENT_PRIMARY, self.BG_SECONDARY, 0.68),
            outline="",
        )
        logo_canvas.create_text(29, 29, text="🎨", font=("Segoe UI Emoji", 20), fill=self.TEXT_PRIMARY)

        header_text = tk.Frame(header_frame, bg=self.BG_PRIMARY)
        header_text.pack(side="left", fill="x", expand=True)

        title = tk.Label(
            header_text,
            text="Frame2File",
            font=("Segoe UI", 28, "bold"),
            bg=self.BG_PRIMARY,
            fg=self.ACCENT_SECONDARY,
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header_text,
            text="Ubah gambar berurutan menjadi PDF profesional",
            font=("Segoe UI", 11),
            bg=self.BG_PRIMARY,
            fg=self.TEXT_SECONDARY,
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        input_section = RoundedFrame(
            main_frame,
            bg=self.BG_PRIMARY,
            fill=self.BG_SECONDARY,
            radius=20,
            padding=(20, 16),
            outline=self.BORDER_SUBTLE,
            shadow=self.SHADOW,
            shadow_offset=4,
            height=106,
        )
        input_section.pack(fill="x", pady=(0, 18))
        input_section_inner = input_section.inner

        folder_label = tk.Label(
            input_section_inner,
            text="📂 Folder Gambar",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG_SECONDARY,
            fg=self.ACCENT_PRIMARY
        )
        folder_label.pack(anchor="w", pady=(0, 10))

        folder_row = tk.Frame(input_section_inner, bg=self.BG_SECONDARY)
        folder_row.pack(fill="x")

        input_wrap = RoundedFrame(
            folder_row,
            bg=self.BG_SECONDARY,
            fill=self.SURFACE_SOFT,
            radius=13,
            padding=(14, 9),
            outline=self.BORDER_SUBTLE,
            height=44,
        )
        input_wrap.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.folder_entry = tk.Entry(
            input_wrap.inner,
            textvariable=self.folder_path,
            state="readonly",
            bg=self.SURFACE_SOFT,
            fg=self.TEXT_PRIMARY,
            readonlybackground=self.SURFACE_SOFT,
            disabledforeground=self.TEXT_PRIMARY,
            insertbackground=self.ACCENT_PRIMARY,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        self.folder_entry.pack(fill="both", expand=True)

        folder_btn = RoundedButton(
            folder_row,
            text="📁 Pilih Folder",
            command=self.choose_folder,
            bg=self.ACCENT_PRIMARY,
            fg=self.BG_PRIMARY,
            hover_bg=self.ACCENT_HOVER,
            active_bg="#4f9ff4",
            radius=13,
            height=44,
            font=("Segoe UI", 9, "bold"),
            width=136,
        )
        folder_btn.pack(side="left")

        preview_section = RoundedFrame(
            main_frame,
            bg=self.BG_PRIMARY,
            fill=self.BG_SECONDARY,
            radius=22,
            padding=(20, 16),
            outline=self.BORDER_SUBTLE,
            shadow=self.SHADOW,
            shadow_offset=4,
            height=560,
        )
        preview_section.pack(fill="both", expand=True, pady=(0, 18))
        preview_inner = preview_section.inner

        preview_header = tk.Frame(preview_inner, bg=self.BG_SECONDARY)
        preview_header.pack(fill="x", pady=(0, 14), padx=(0, 18))
        preview_header.columnconfigure(0, weight=1)

        preview_title_block = tk.Frame(preview_header, bg=self.BG_SECONDARY)
        preview_title_block.grid(row=0, column=0, sticky="ew")

        preview_label = tk.Label(
            preview_title_block,
            text="🖼️ Preview Gambar",
            font=("Segoe UI", 11, "bold"),
            bg=self.BG_SECONDARY,
            fg=self.TEXT_PRIMARY,
        )
        preview_label.pack(anchor="w")

        preview_hint = tk.Label(
            preview_title_block,
            text="Drag thumbnail untuk mengubah urutan",
            font=("Segoe UI", 9),
            bg=self.BG_SECONDARY,
            fg=self.TEXT_MUTED,
        )
        preview_hint.pack(anchor="w", pady=(2, 0))

        control_row = tk.Frame(preview_header, bg=self.BG_SECONDARY)
        control_row.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.add_button = self.create_small_button(control_row, "Tambah", self.add_images)
        self.up_button = self.create_small_button(control_row, "Naik", lambda: self.move_selected(-1))
        self.down_button = self.create_small_button(control_row, "Turun", lambda: self.move_selected(1))
        self.delete_button = self.create_small_button(control_row, "Hapus", self.delete_selected, self.DANGER)
        self.action_buttons = [self.add_button, self.up_button, self.down_button, self.delete_button]
        control_row.bind("<Configure>", lambda event: self.layout_action_buttons(control_row, event.width))
        self.layout_action_buttons(control_row, 900)

        preview_body = tk.Frame(preview_inner, bg=self.BG_SECONDARY)
        preview_body.pack(fill="both", expand=True)

        self.preview_canvas = tk.Canvas(
            preview_body,
            bg=self.BG_SECONDARY,
            bd=0,
            highlightthickness=0,
            yscrollincrement=16,
        )
        self.preview_canvas.pack(side="left", fill="both", expand=True)

        self.preview_scrollbar = tk.Canvas(
            preview_body,
            width=10,
            bg=self.SURFACE_SOFT,
            highlightthickness=0,
            bd=0,
        )
        self.preview_scrollbar.pack(side="right", fill="y", padx=(12, 0))
        self.preview_scrollbar.bind("<Button-1>", self.on_scrollbar_press)
        self.preview_scrollbar.bind("<B1-Motion>", self.on_scrollbar_drag)
        self.preview_scrollbar.bind("<ButtonRelease-1>", lambda _event: setattr(self, "scrollbar_dragging", False))
        self.preview_scrollbar.bind("<Enter>", lambda _event: self.draw_preview_scrollbar(True))
        self.preview_scrollbar.bind("<Leave>", lambda _event: self.draw_preview_scrollbar(False))
        self.preview_scrollbar.bind("<Configure>", lambda _event: self.draw_preview_scrollbar(False))
        self.preview_canvas.configure(yscrollcommand=self.update_preview_scrollbar)

        self.preview_inner = tk.Frame(self.preview_canvas, bg=self.BG_SECONDARY)
        self.preview_window = self.preview_canvas.create_window(
            (0, 0),
            window=self.preview_inner,
            anchor="nw",
        )
        self.preview_inner.bind(
            "<Configure>",
            lambda _event: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all")),
        )
        self.preview_canvas.bind(
            "<Configure>",
            self.on_preview_resize,
        )
        self.preview_canvas.bind("<MouseWheel>", self.on_preview_mousewheel)

        progress_frame = RoundedFrame(
            main_frame,
            bg=self.BG_PRIMARY,
            fill=self.BG_SECONDARY,
            radius=18,
            padding=(18, 10),
            outline=self.BORDER_SUBTLE,
            shadow=self.SHADOW,
            shadow_offset=3,
            height=54,
        )
        progress_frame.pack(fill="x", pady=(0, 16))
        progress_inner = progress_frame.inner

        self.progress_track = tk.Canvas(
            progress_inner,
            height=7,
            bg=self.BG_SECONDARY,
            bd=0,
            highlightthickness=0,
        )
        self.progress_track.pack(fill="x", pady=(0, 7))
        self.progress_track.bind("<Configure>", lambda _event: self.set_progress_bar(self.progress_value.get()))

        status_label = tk.Label(
            progress_inner,
            textvariable=self.status_text,
            font=("Segoe UI", 9, "bold"),
            bg=self.BG_SECONDARY,
            fg=self.TEXT_SECONDARY,
            wraplength=860,
            justify="left",
        )
        status_label.pack(anchor="w")

        self.convert_button = RoundedButton(
            main_frame,
            text="✨ Buat PDF",
            command=self.start_conversion,
            bg=self.SUCCESS,
            fg=self.BG_PRIMARY,
            hover_bg=self.SUCCESS_HOVER,
            active_bg=self.SUCCESS_ACTIVE,
            radius=16,
            height=54,
            font=("Segoe UI", 12, "bold"),
        )
        self.convert_button.pack(fill="x", pady=(0, 14))

        footer_frame = tk.Frame(main_frame, bg=self.BG_PRIMARY)
        footer_frame.pack(fill="x")

        footer_text = tk.Label(
            footer_frame,
            text="📸 Format didukung: JPG • JPEG • PNG • WEBP • BMP",
            font=("Segoe UI", 9),
            bg=self.BG_PRIMARY,
            fg=self.TEXT_MUTED
        )
        footer_text.pack(anchor="w")

    def create_small_button(
        self,
        parent: tk.Frame,
        text: str,
        command,
        color: Optional[str] = None,
    ) -> RoundedButton:
        is_danger = color == self.DANGER
        button = RoundedButton(
            parent,
            text=text,
            command=command,
            bg=color or self.SURFACE_SOFT,
            fg=self.TEXT_PRIMARY if is_danger else self.ACCENT_SECONDARY,
            hover_bg=self.DANGER_HOVER if is_danger else blend_colors(self.SURFACE_SOFT, self.ACCENT_PRIMARY, 0.18),
            active_bg=self.DANGER_ACTIVE if is_danger else blend_colors(self.SURFACE_SOFT, self.ACCENT_PRIMARY, 0.28),
            radius=10,
            height=34,
            font=("Segoe UI", 8, "bold"),
            width=128,
        )
        return button

    def layout_action_buttons(self, parent: tk.Frame, available_width: int) -> None:
        for button in self.action_buttons:
            button.grid_forget()

        columns = 4 if available_width >= 560 else 2
        for column in range(6):
            parent.columnconfigure(column, weight=0)
        parent.columnconfigure(0, weight=1)

        for index, button in enumerate(self.action_buttons):
            button.grid(
                row=index // columns,
                column=index % columns + 1,
                padx=(12 if index % columns else 0, 0),
                pady=(0 if index < columns else 8, 0),
                sticky="e",
            )

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Pilih folder gambar")
        if not selected:
            return

        folder = Path(selected)
        images = find_images(folder)

        self.folder_path.set(str(folder))
        self.output_path.set(str(folder / f"{folder.name}.pdf"))
        self.set_images(images)
        if images:
            self.status_text.set(f"✅ Ditemukan {len(images)} gambar siap diproses")
        else:
            self.status_text.set("❌ Tidak ada gambar yang didukung di folder ini")

    def set_images(self, images: List[Path]) -> None:
        self.image_paths = list(images)
        self.selected_index = 0 if self.image_paths else None
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.render_preview()

    def add_images(self) -> None:
        filetypes = [
            ("Gambar", "*.jpg *.jpeg *.png *.webp *.bmp"),
            ("JPG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("WEBP", "*.webp"),
            ("BMP", "*.bmp"),
        ]
        selected = filedialog.askopenfilenames(
            title="Tambah gambar",
            filetypes=filetypes,
        )
        if not selected:
            return

        added = [Path(path) for path in selected]
        self.image_paths.extend(added)

        if not self.folder_path.get() and added:
            folder = added[0].parent
            self.folder_path.set(str(folder))
            self.output_path.set(str(folder / f"{folder.name}.pdf"))

        self.selected_index = len(self.image_paths) - len(added)
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.render_preview()
        self.status_text.set(f"✅ Total {len(self.image_paths)} gambar siap diproses")

    def select_image(self, index: int) -> None:
        self.selected_index = index
        self.render_preview()

    def start_drag(self, event: tk.Event, index: int) -> None:
        self.drag_start_index = index
        self.selected_index = index
        self.create_drag_ghost(index, event.x_root, event.y_root)
        self.dim_drag_source(index)

    def update_drag(self, event: tk.Event) -> None:
        if self.drag_start_index is None:
            return

        self.move_drag_ghost(event.x_root, event.y_root)
        self.drop_insert_index = self.get_drop_insert_index(event.x_root, event.y_root)
        self.draw_drop_indicator(self.drop_insert_index)

    def finish_drag(self, event: tk.Event) -> None:
        if self.drag_start_index is None:
            self.clear_drag_visuals()
            return

        insert_index = self.get_drop_insert_index(event.x_root, event.y_root)
        start_index = self.drag_start_index
        self.drag_start_index = None
        self.clear_drag_visuals()

        if insert_index is None or insert_index in (start_index, start_index + 1):
            self.selected_index = start_index
            self.render_preview()
            return

        image_path = self.image_paths.pop(start_index)
        if insert_index > start_index:
            insert_index -= 1

        insert_index = max(0, min(insert_index, len(self.image_paths)))
        self.image_paths.insert(insert_index, image_path)
        self.selected_index = insert_index
        self.flash_index = insert_index
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.render_preview()
        self.status_text.set("✅ Urutan gambar diperbarui")
        self.root.after(550, self.clear_flash_highlight)

    def get_drop_index(self, pointer_x: int, pointer_y: int) -> Optional[int]:
        if not self.preview_items:
            return None

        nearest_index = None
        nearest_distance = None

        for index, item in enumerate(self.preview_items):
            left = item.winfo_rootx()
            top = item.winfo_rooty()
            right = left + item.winfo_width()
            bottom = top + item.winfo_height()

            if left <= pointer_x <= right and top <= pointer_y <= bottom:
                return index

            center_x = left + item.winfo_width() / 2
            center_y = top + item.winfo_height() / 2
            distance = (pointer_x - center_x) ** 2 + (pointer_y - center_y) ** 2
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_index = index

        return nearest_index

    def get_drop_insert_index(self, pointer_x: int, pointer_y: int) -> Optional[int]:
        if not self.preview_items:
            return None

        nearest_index = self.get_drop_index(pointer_x, pointer_y)
        if nearest_index is None:
            return None

        item = self.preview_items[nearest_index]
        center_x = item.winfo_rootx() + item.winfo_width() / 2
        return nearest_index if pointer_x < center_x else nearest_index + 1

    def draw_drop_indicator(self, insert_index: Optional[int]) -> None:
        self.destroy_drop_indicator()
        if insert_index is None or not self.preview_items:
            return

        index = min(insert_index, len(self.preview_items) - 1)
        item = self.preview_items[index]
        item_left = item.winfo_x()
        item_top = item.winfo_y()
        item_bottom = item_top + item.winfo_height()
        x = item_left - 7

        if insert_index >= len(self.preview_items):
            x = item_left + item.winfo_width() + 7

        self.drop_indicator_widget = tk.Frame(
            self.preview_inner,
            bg=blend_colors(self.ACCENT_PRIMARY, self.BG_SECONDARY, 0.12),
            width=5,
            height=max(item_bottom - item_top - 14, 20),
            bd=0,
            highlightthickness=1,
            highlightbackground=blend_colors(self.ACCENT_PRIMARY, self.TEXT_PRIMARY, 0.2),
        )
        self.drop_indicator_widget.place(
            x=max(x, 0),
            y=item_top + 7,
        )

    def destroy_drop_indicator(self) -> None:
        if self.drop_indicator_widget is not None:
            try:
                self.drop_indicator_widget.destroy()
            except tk.TclError:
                pass
        self.drop_indicator_widget = None

    def create_drag_ghost(self, index: int, pointer_x: int, pointer_y: int) -> None:
        self.destroy_drag_ghost()
        if index < 0 or index >= len(self.image_paths):
            return

        self.drag_ghost = tk.Toplevel(self.root)
        self.drag_ghost.overrideredirect(True)
        self.drag_ghost.attributes("-topmost", True)
        try:
            self.drag_ghost.attributes("-alpha", 0.82)
        except tk.TclError:
            pass

        self.drag_ghost_photo = self.create_thumbnail(self.image_paths[index])
        ghost_frame = tk.Frame(self.drag_ghost, bg=self.SURFACE_ELEVATED, bd=0, highlightthickness=1, highlightbackground=self.ACCENT_PRIMARY)
        ghost_frame.pack(padx=1, pady=1)
        tk.Label(ghost_frame, image=self.drag_ghost_photo, bg=self.SURFACE_ELEVATED, bd=0).pack(padx=8, pady=8)
        self.move_drag_ghost(pointer_x, pointer_y)

    def move_drag_ghost(self, pointer_x: int, pointer_y: int) -> None:
        if self.drag_ghost is None:
            return
        self.drag_ghost.geometry(f"+{pointer_x + 14}+{pointer_y + 14}")

    def destroy_drag_ghost(self) -> None:
        if self.drag_ghost is not None:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
        self.drag_ghost = None
        self.drag_ghost_photo = None

    def dim_drag_source(self, index: int) -> None:
        if index < 0 or index >= len(self.preview_items):
            return
        item = self.preview_items[index]
        if isinstance(item, RoundedFrame):
            item.set_style(
                fill=blend_colors(self.SURFACE_ELEVATED, self.BG_PRIMARY, 0.38),
                outline=blend_colors(self.ACCENT_PRIMARY, self.BG_SECONDARY, 0.45),
                shadow="",
            )

    def clear_drag_visuals(self) -> None:
        self.destroy_drag_ghost()
        self.drop_insert_index = None
        self.destroy_drop_indicator()

    def clear_flash_highlight(self) -> None:
        if self.flash_index is None:
            return
        self.flash_index = None
        self.render_preview()

    def bind_drag_events(self, widget: tk.Widget, index: int) -> None:
        widget.bind("<Button-1>", lambda event, i=index: self.start_drag(event, i))
        widget.bind("<B1-Motion>", self.update_drag)
        widget.bind("<ButtonRelease-1>", self.finish_drag)
        widget.bind("<MouseWheel>", self.on_preview_mousewheel)

    def bind_card_hover(
        self,
        widget: tk.Widget,
        index: int,
        fill_color: str,
        border_color: str,
        card: Optional[RoundedFrame] = None,
    ) -> None:
        target = card or widget
        if not isinstance(target, RoundedFrame):
            return

        def on_enter(_event: tk.Event) -> None:
            if self.drag_start_index is not None:
                return
            target.set_style(
                fill=blend_colors(fill_color, self.ACCENT_PRIMARY, 0.07),
                outline=blend_colors(border_color, self.ACCENT_PRIMARY, 0.32),
                shadow=self.SHADOW,
            )

        def on_leave(_event: tk.Event) -> None:
            if self.drag_start_index is not None:
                return
            target.set_style(
                fill=fill_color,
                outline=border_color,
                shadow=self.SHADOW if index == self.selected_index or index == self.flash_index else "",
            )

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def move_selected(self, direction: int) -> None:
        if self.selected_index is None:
            return

        new_index = self.selected_index + direction
        if new_index < 0 or new_index >= len(self.image_paths):
            return

        current = self.selected_index
        self.image_paths[current], self.image_paths[new_index] = (
            self.image_paths[new_index],
            self.image_paths[current],
        )
        self.selected_index = new_index
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.render_preview()
        self.status_text.set("✅ Urutan gambar diperbarui")

    def delete_selected(self) -> None:
        if self.selected_index is None:
            return

        removed = self.image_paths.pop(self.selected_index)
        if not self.image_paths:
            self.selected_index = None
        else:
            self.selected_index = min(self.selected_index, len(self.image_paths) - 1)

        self.render_preview()
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.status_text.set(f"🗑️ Dihapus: {removed.name}")

    def render_preview(self) -> None:
        for widget in self.preview_inner.winfo_children():
            widget.destroy()

        self.thumbnail_refs.clear()
        self.preview_items.clear()

        if not self.image_paths:
            empty_label = tk.Label(
                self.preview_inner,
                text="Belum ada gambar",
                font=("Segoe UI", 11, "bold"),
                bg=self.BG_SECONDARY,
                fg=self.TEXT_SECONDARY,
            )
            empty_label.pack(padx=12, pady=138)
            empty_label.bind("<MouseWheel>", self.on_preview_mousewheel)
            self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
            return

        canvas_width = max(self.preview_canvas.winfo_width(), 640)
        columns = max(1, canvas_width // 246)

        for index, image_path in enumerate(self.image_paths):
            is_selected = index == self.selected_index
            is_flash = index == self.flash_index
            border_color = blend_colors(self.ACCENT_PRIMARY, self.BG_SECONDARY, 0.18) if is_selected else self.BORDER_SUBTLE
            fill_color = blend_colors(self.SURFACE_ELEVATED, self.ACCENT_PRIMARY, 0.08) if is_selected else self.SURFACE_ELEVATED
            if is_flash:
                border_color = self.SUCCESS
                fill_color = blend_colors(self.SURFACE_ELEVATED, self.SUCCESS, 0.16)
            item = RoundedFrame(
                self.preview_inner,
                bg=self.BG_SECONDARY,
                fill=fill_color,
                radius=16,
                padding=(12, 12),
                outline=border_color,
                shadow=self.SHADOW if is_selected or is_flash else "",
                shadow_offset=2 if is_selected or is_flash else 0,
                width=228,
                height=292,
            )
            item.grid(
                row=index // columns,
                column=index % columns,
                padx=(0, 18),
                pady=(0, 20),
                sticky="nw",
            )
            self.preview_items.append(item)
            self.bind_drag_events(item, index)
            self.bind_drag_events(item.canvas, index)
            self.bind_drag_events(item.inner, index)
            self.bind_card_hover(item, index, fill_color, border_color)

            photo = self.create_thumbnail(image_path)
            self.thumbnail_refs.append(photo)

            image_label = tk.Label(
                item.inner,
                image=photo,
                bg=fill_color,
                bd=0,
                cursor="hand2",
            )
            image_label.pack(pady=(0, 9))
            self.bind_drag_events(image_label, index)
            self.bind_card_hover(image_label, index, fill_color, border_color, item)

            name_label = tk.Label(
                item.inner,
                text=f"{index + 1}. {image_path.name}",
                font=("Segoe UI", 9, "bold"),
                bg=fill_color,
                fg=self.TEXT_PRIMARY if is_selected else self.TEXT_SECONDARY,
                wraplength=198,
                justify="center",
                cursor="hand2",
            )
            name_label.pack(fill="x", padx=6)
            self.bind_drag_events(name_label, index)
            self.bind_card_hover(name_label, index, fill_color, border_color, item)

        self.preview_inner.update_idletasks()
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def on_preview_resize(self, event: tk.Event) -> None:
        self.preview_canvas.itemconfigure(self.preview_window, width=event.width)
        self.root.after_idle(self.render_preview)

    def on_preview_mousewheel(self, event: tk.Event) -> None:
        self.preview_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_preview_scrollbar(self, first: str, last: str) -> None:
        self.scrollbar_first = float(first)
        self.scrollbar_last = float(last)
        self.draw_preview_scrollbar(False)

    def draw_preview_scrollbar(self, hover: bool = False) -> None:
        self.preview_scrollbar.delete("all")
        width = max(self.preview_scrollbar.winfo_width(), 8)
        height = max(self.preview_scrollbar.winfo_height(), 1)
        track_x = width // 2 - 3

        draw_rounded_rect(
            self.preview_scrollbar,
            track_x,
            0,
            track_x + 6,
            height,
            3,
            fill=blend_colors(self.BG_SECONDARY, self.SURFACE_SOFT, 0.55),
            outline="",
        )

        if self.scrollbar_last - self.scrollbar_first >= 0.999:
            return

        thumb_min = 38
        thumb_top = int(height * self.scrollbar_first)
        thumb_bottom = int(height * self.scrollbar_last)
        if thumb_bottom - thumb_top < thumb_min:
            thumb_bottom = min(height, thumb_top + thumb_min)

        thumb_color = blend_colors(self.SURFACE_SOFT, self.ACCENT_PRIMARY, 0.28 if hover else 0.18)
        self.scroll_thumb_id = draw_rounded_rect(
            self.preview_scrollbar,
            track_x,
            thumb_top,
            track_x + 6,
            thumb_bottom,
            3,
            fill=thumb_color,
            outline="",
        )

    def on_scrollbar_press(self, event: tk.Event) -> None:
        self.scrollbar_dragging = True
        self.move_preview_scrollbar(event.y)

    def on_scrollbar_drag(self, event: tk.Event) -> None:
        if self.scrollbar_dragging:
            self.move_preview_scrollbar(event.y)

    def move_preview_scrollbar(self, y: int) -> None:
        height = max(self.preview_scrollbar.winfo_height(), 1)
        visible_span = max(self.scrollbar_last - self.scrollbar_first, 0.05)
        target = min(max(y / height - visible_span / 2, 0.0), 1.0 - visible_span)
        self.preview_canvas.yview_moveto(target)

    def create_thumbnail(self, image_path: Path) -> ImageTk.PhotoImage:
        try:
            with Image.open(image_path) as source:
                preview = source.copy()
                preview.thumbnail((198, 222), THUMBNAIL_FILTER)
                background = Image.new("RGB", (198, 222), self.BG_PRIMARY)
                x = (198 - preview.width) // 2
                y = (222 - preview.height) // 2

                if preview.mode in ("RGBA", "LA") or (
                    preview.mode == "P" and "transparency" in preview.info
                ):
                    rgba = preview.convert("RGBA")
                    background.paste(rgba, (x, y), rgba.getchannel("A"))
                else:
                    background.paste(preview.convert("RGB"), (x, y))

                return ImageTk.PhotoImage(background)
        except Exception:
            fallback = Image.new("RGB", (198, 222), self.SURFACE_SOFT)
            return ImageTk.PhotoImage(fallback)

    def start_conversion(self) -> None:
        folder_text = self.folder_path.get()

        if not folder_text:
            messagebox.showwarning("Belum ada folder", "📂 Silakan pilih folder gambar terlebih dahulu.")
            return

        folder = Path(folder_text)
        output_file = folder / f"{folder.name}.pdf"
        self.output_path.set(str(output_file))
        images = list(self.image_paths)

        if not images:
            messagebox.showwarning(
                "Tidak ada gambar",
                "❌ Folder ini tidak berisi JPG, JPEG, PNG, WEBP, atau BMP."
            )
            return

        self.convert_button.config(state="disabled")
        self.progress_value.set(0)
        self.set_progress_bar(0)
        self.status_text.set(f"⚙️ Membuat PDF dari {len(images)} gambar...")

        worker = threading.Thread(
            target=self.convert_images,
            args=(images, output_file),
            daemon=True,
        )
        worker.start()

    def convert_images(self, images: List[Path], output_file: Path) -> None:
        pages: List[Image.Image] = []

        try:
            for index, image_path in enumerate(images, start=1):
                with Image.open(image_path) as source:
                    if source.mode in ("RGBA", "LA") or (
                        source.mode == "P" and "transparency" in source.info
                    ):
                        background = Image.new("RGB", source.size, "white")
                        rgba = source.convert("RGBA")
                        background.paste(rgba, mask=rgba.getchannel("A"))
                        page = background
                    else:
                        page = source.convert("RGB")

                    pages.append(page.copy())

                progress = int(index / len(images) * 100)
                self.root.after(
                    0,
                    lambda p=progress, i=index: self.update_progress(p, i, len(images))
                )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            pages[0].save(
                output_file,
                "PDF",
                save_all=True,
                append_images=pages[1:],
                resolution=150.0,
            )

            self.root.after(
                0,
                lambda: self.finish_success(output_file, len(images))
            )

        except Exception as exc:
            self.root.after(0, lambda: self.finish_error(str(exc)))

        finally:
            for page in pages:
                page.close()

    def update_progress(self, progress: int, current: int, total: int) -> None:
        self.progress_value.set(progress)
        self.set_progress_bar(progress)
        self.status_text.set(f"⏳ Memproses gambar {current} dari {total}...")

    def finish_success(self, output_file: Path, total: int) -> None:
        self.progress_value.set(100)
        self.set_progress_bar(100)
        self.status_text.set(f"✅ Selesai! {total} gambar disimpan ke {output_file}")
        self.convert_button.config(state="normal")

    def finish_error(self, error: str) -> None:
        self.status_text.set("❌ Gagal membuat PDF.")
        self.convert_button.config(state="normal")
        messagebox.showerror("⚠️ Terjadi kesalahan", error)

    def set_progress_bar(self, progress: int) -> None:
        self.progress_track.update_idletasks()
        track_width = self.progress_track.winfo_width()
        track_height = self.progress_track.winfo_height()
        fill_width = int(track_width * max(0, min(progress, 100)) / 100)
        self.progress_track.delete("all")
        if progress <= 0:
            return
        draw_rounded_rect(
            self.progress_track,
            0,
            0,
            track_width,
            track_height,
            4,
            fill=self.SURFACE_SOFT,
            outline="",
        )
        if fill_width > 0:
            draw_rounded_rect(
                self.progress_track,
                0,
                0,
                fill_width,
                track_height,
                4,
                fill=self.SUCCESS,
                outline="",
            )


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg="#080d14")
    
    # Try to set icon if available
    try:
        root.iconbitmap(default='')
    except:
        pass

    app = Frame2FileApp(root)
    root.mainloop()
