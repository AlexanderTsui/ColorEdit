#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image preview panel."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class ImagePreviewPanel:
    """Panel for source image/camera preview."""

    def __init__(self, parent: tk.Widget, on_image_loaded: Optional[Callable] = None):
        self.parent = parent
        self.on_image_loaded = on_image_loaded

        self.current_image = None
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0

        self.setup_ui()
        logger.debug("Image preview panel initialized")

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.parent, style="Panel.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_toolbar()
        self.create_image_display()
        self.create_status_info()

    def create_toolbar(self) -> None:
        toolbar = ttk.Frame(self.main_frame, style="Panel.TFrame")
        toolbar.pack(fill=tk.X, pady=(0, 8))

        ttk.Button(toolbar, text="Load Image", command=self.load_image_file).pack(side=tk.LEFT, padx=(0, 6))

        self.camera_btn = ttk.Button(toolbar, text="Start Camera", command=self.toggle_camera)
        self.camera_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

        ttk.Label(toolbar, text="Zoom", style="Subtle.TLabel").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="-", width=3, command=self.zoom_out).pack(side=tk.LEFT, padx=(6, 2))

        self.zoom_var = tk.StringVar(value="100%")
        ttk.Label(toolbar, textvariable=self.zoom_var, width=6).pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT, padx=(2, 6))
        ttk.Button(toolbar, text="Reset", command=self.reset_view).pack(side=tk.LEFT)

    def create_image_display(self) -> None:
        canvas_frame = ttk.Frame(self.main_frame, style="Panel.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg="#0b111f", highlightthickness=1, highlightbackground="#24375f")

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_canvas_wheel)
        self.canvas.bind("<Button-4>", self.on_canvas_wheel)
        self.canvas.bind("<Button-5>", self.on_canvas_wheel)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.show_placeholder_text()

    def create_status_info(self) -> None:
        status_frame = ttk.Frame(self.main_frame, style="Panel.TFrame")
        status_frame.pack(fill=tk.X, pady=(8, 0))

        self.info_var = tk.StringVar(value="Load an image or start camera")
        ttk.Label(status_frame, textvariable=self.info_var, style="Subtle.TLabel").pack(side=tk.LEFT)

    def show_placeholder_text(self) -> None:
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            self.canvas.create_text(
                center_x,
                center_y - 16,
                text="Drop or open an image",
                fill="#6e84b8",
                font=("Segoe UI", 14, "bold"),
            )
            self.canvas.create_text(
                center_x,
                center_y + 16,
                text="Mask preview updates in real time while tuning HSV",
                fill="#4f6599",
                font=("Segoe UI", 10),
            )

    def load_image_file(self) -> None:
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("All files", "*.*"),
        ]

        filename = filedialog.askopenfilename(title="Select image file", filetypes=file_types)
        if filename:
            self.load_image_from_file(filename)

    def load_image_from_file(self, filename: str) -> None:
        try:
            image = cv2.imread(filename)
            if image is None:
                raise ValueError("Unable to read image file")

            self.update_image(image)
            height, width = image.shape[:2]
            self.info_var.set(f"Image: {width}x{height} - {filename}")

            if self.on_image_loaded:
                self.on_image_loaded(image)

            logger.info("Image loaded: %s", filename)
        except Exception as e:
            logger.error("Failed to load image: %s", e)
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def update_image(self, image: np.ndarray) -> None:
        try:
            self.current_image = image.copy()
            self.display_image_on_canvas()
        except Exception as e:
            logger.error("Failed to update image display: %s", e)

    def display_image_on_canvas(self) -> None:
        if self.current_image is None:
            return

        try:
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            height, width = rgb_image.shape[:2]

            new_width = int(width * self.zoom_level)
            new_height = int(height * self.zoom_level)
            if self.zoom_level != 1.0:
                interp = cv2.INTER_AREA if self.zoom_level < 1.0 else cv2.INTER_CUBIC
                rgb_image = cv2.resize(rgb_image, (new_width, new_height), interpolation=interp)

            pil_image = Image.fromarray(rgb_image)
            tk_image = ImageTk.PhotoImage(pil_image)

            self.canvas.delete("all")
            self.image_id = self.canvas.create_image(self.pan_x, self.pan_y, anchor=tk.NW, image=tk_image)
            self.canvas.image = tk_image
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
        except Exception as e:
            logger.error("Failed to render image: %s", e)

    def zoom_in(self) -> None:
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.display_image_on_canvas()

    def zoom_out(self) -> None:
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.display_image_on_canvas()

    def reset_view(self) -> None:
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_image_on_canvas()

    def on_canvas_click(self, event) -> None:
        self.last_x = event.x
        self.last_y = event.y

    def on_canvas_drag(self, event) -> None:
        if hasattr(self, "last_x") and hasattr(self, "last_y"):
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            self.pan_x += dx
            self.pan_y += dy

            if hasattr(self, "image_id"):
                self.canvas.move(self.image_id, dx, dy)

            self.last_x = event.x
            self.last_y = event.y

    def on_canvas_wheel(self, event) -> None:
        if (hasattr(event, "delta") and event.delta > 0) or getattr(event, "num", None) == 4:
            self.zoom_in()
        else:
            self.zoom_out()

    def on_canvas_configure(self, _event) -> None:
        if self.current_image is None:
            self.show_placeholder_text()

    def toggle_camera(self) -> None:
        # Camera start/stop is handled by the main window; this only reflects state.
        self.set_camera_active(self.camera_btn.cget("text") == "Start Camera")

    def set_camera_active(self, active: bool) -> None:
        self.camera_btn.configure(text="Stop Camera" if active else "Start Camera")

    def update_info(self, info_text: str) -> None:
        self.info_var.set(info_text)

    def get_current_image(self) -> Optional[np.ndarray]:
        return self.current_image
