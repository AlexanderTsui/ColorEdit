#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main application window for ColorEdit."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import threading
import logging
from typing import Dict, Tuple

from src.core.image_processor import ImageProcessor
from src.core.camera_manager import CameraManager
from src.core.config_manager import ConfigManager
from src.gui.hsv_control_panel import HSVControlPanel
from src.gui.image_preview_panel import ImagePreviewPanel
from src.gui.mask_preview_panel import MaskPreviewPanel
from src.gui.status_bar import StatusBar

logger = logging.getLogger(__name__)


class ColorEditMainWindow:
    """Main application UI."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()

        self.image_processor = ImageProcessor()
        self.config_manager = ConfigManager()
        self.camera_manager = CameraManager(self.on_camera_frame)

        self.current_image = None
        self.current_threshold = self.config_manager.get_default_threshold()
        self.current_mask = None
        self.processing_lock = threading.Lock()

        self.setup_menu()
        self.setup_ui()
        self.setup_bindings()

        self.config_manager.load_presets()
        logger.info("Main window initialized")

    def setup_window(self) -> None:
        self.root.title("ColorEdit - HSV Threshold Editor")
        self.root.geometry("1320x840")
        self.root.minsize(960, 640)
        self.root.configure(bg="#0e1320")
        self.setup_style()
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def setup_style(self) -> None:
        style = ttk.Style()
        theme = "clam" if "clam" in style.theme_names() else style.theme_use()
        style.theme_use(theme)

        bg = "#0e1320"
        panel = "#141c2f"
        panel_alt = "#1b2742"
        fg = "#eaf1ff"
        accent = "#12d6ff"
        subtle = "#96a7d4"

        style.configure("TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)

        style.configure("Card.TLabelframe", background=panel, borderwidth=1, relief=tk.SOLID)
        style.configure("Card.TLabelframe.Label", background=panel, foreground=accent, font=("Segoe UI", 10, "bold"))

        style.configure("Toolbar.TFrame", background=panel_alt)
        style.configure("Header.TLabel", background=panel_alt, foreground=fg, font=("Segoe UI", 11, "bold"))
        style.configure("Subtle.TLabel", background=panel_alt, foreground=subtle, font=("Segoe UI", 9))

        style.configure("Toolbar.TButton", padding=(10, 6))
        style.configure("Accent.TButton", padding=(10, 6), foreground="#001018")
        style.map(
            "Accent.TButton",
            background=[("!disabled", accent), ("active", "#58e6ff"), ("pressed", "#00b7dd")],
            foreground=[("!disabled", "#001018")],
        )

        style.configure("TNotebook", background=panel, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(10, 6))

    def setup_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image", command=self.open_image_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save Config", command=self.save_config, accelerator="Ctrl+S")
        file_menu.add_command(label="Load Config", command=self.load_config, accelerator="Ctrl+L")
        file_menu.add_command(label="Export Config", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_window_close, accelerator="Ctrl+Q")

        camera_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Camera", menu=camera_menu)
        camera_menu.add_command(label="Start Camera", command=self.start_camera)
        camera_menu.add_command(label="Stop Camera", command=self.stop_camera)
        camera_menu.add_separator()
        camera_menu.add_command(label="Camera Settings", command=self.show_camera_settings)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reset Threshold", command=self.reset_threshold)
        tools_menu.add_command(label="Color Presets", command=self.show_color_presets)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Usage", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_ui(self) -> None:
        top = ttk.Frame(self.root, style="Toolbar.TFrame")
        top.pack(fill=tk.X, padx=8, pady=(8, 6))

        ttk.Label(top, text="ColorEdit", style="Header.TLabel").pack(side=tk.LEFT, padx=(10, 12))
        ttk.Label(top, text="Tune HSV thresholds and preview mask in real time", style="Subtle.TLabel").pack(side=tk.LEFT)

        actions = ttk.Frame(top, style="Toolbar.TFrame")
        actions.pack(side=tk.RIGHT, padx=6)
        ttk.Button(actions, text="Open Image", style="Toolbar.TButton", command=self.open_image_file).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Start Camera", style="Accent.TButton", command=self.start_camera).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Stop Camera", style="Toolbar.TButton", command=self.stop_camera).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Save", style="Toolbar.TButton", command=self.save_config).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Load", style="Toolbar.TButton", command=self.load_config).pack(side=tk.LEFT, padx=3)

        body = ttk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        panes = ttk.Panedwindow(body, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(panes, text="Image Feed", padding=8, style="Card.TLabelframe")
        middle = ttk.LabelFrame(panes, text="HSV Controls", padding=8, style="Card.TLabelframe")
        right = ttk.LabelFrame(panes, text="Mask Analysis", padding=8, style="Card.TLabelframe")
        panes.add(left, weight=4)
        panes.add(middle, weight=2)
        panes.add(right, weight=4)

        self.image_preview = ImagePreviewPanel(left, self.on_image_loaded)
        self.hsv_control = HSVControlPanel(middle, self.current_threshold, self.on_threshold_changed)
        self.mask_preview = MaskPreviewPanel(right)

        self.status_bar = StatusBar(self.root)
        self.update_displays()

    def setup_bindings(self) -> None:
        self.root.bind("<Control-o>", lambda e: self.open_image_file())
        self.root.bind("<Control-s>", lambda e: self.save_config())
        self.root.bind("<Control-l>", lambda e: self.load_config())
        self.root.bind("<Control-q>", lambda e: self.on_window_close())
        self.root.bind("<F5>", lambda e: self.process_current_image())
        self.root.bind("<space>", lambda e: self.toggle_camera())

    def on_camera_frame(self, frame: np.ndarray) -> None:
        try:
            self.current_image = frame.copy()
            self.image_preview.update_image(frame)
            self.process_current_image()

            camera_info = self.camera_manager.get_camera_info()
            if camera_info:
                self.status_bar.update_status(f"Camera running - FPS: {camera_info.get('current_fps', 0)}")
        except Exception as e:
            logger.error("Failed to process camera frame: %s", e)

    def on_image_loaded(self, image: np.ndarray) -> None:
        self.current_image = image
        self.process_current_image()
        self.status_bar.update_status("Image loaded")

    def on_threshold_changed(self, threshold: Dict[str, Tuple[int, int]]) -> None:
        self.current_threshold = threshold
        self.process_current_image()

    def process_current_image(self) -> None:
        if self.current_image is None:
            return

        if not self.processing_lock.acquire(blocking=False):
            return

        try:
            mask = self.image_processor.create_mask(self.current_image, self.current_threshold)
            self.current_mask = mask
            self.mask_preview.update_mask(mask)

            hsv_image = self.image_processor.convert_to_hsv(self.current_image)
            histogram = self.image_processor.calculate_histogram(hsv_image)
            self.mask_preview.update_histogram(histogram)

            stats = self.image_processor.get_mask_statistics(mask, self.current_image.shape[:2])
            self.mask_preview.update_statistics(stats)
        except Exception as e:
            logger.error("Image processing failed: %s", e)
            messagebox.showerror("Error", f"Image processing failed: {e}")
        finally:
            self.processing_lock.release()

    def open_image_file(self) -> None:
        file_types = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("BMP", "*.bmp"),
            ("All files", "*.*"),
        ]

        filename = filedialog.askopenfilename(title="Select image file", filetypes=file_types)
        if not filename:
            return

        try:
            if self.camera_manager.is_camera_active():
                self.camera_manager.stop_camera()
                self.image_preview.set_camera_active(False)

            image = cv2.imread(filename)
            if image is None:
                raise ValueError("Unable to read image file")

            image = self.image_processor.resize_image(image)
            self.image_preview.update_image(image)
            self.current_image = image
            self.process_current_image()

            self.status_bar.update_status(f"Loaded image: {filename}")
            logger.info("Image loaded: %s", filename)
        except Exception as e:
            logger.error("Failed to load image: %s", e)
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def start_camera(self) -> None:
        try:
            if self.camera_manager.start_camera():
                self.image_preview.set_camera_active(True)
                self.status_bar.update_status("Camera started")
                logger.info("Camera started")
            else:
                error_msg = self.camera_manager.get_error_message()
                messagebox.showerror("Error", f"Failed to start camera: {error_msg}")
        except Exception as e:
            logger.error("Failed to start camera: %s", e)
            messagebox.showerror("Error", f"Failed to start camera: {e}")

    def stop_camera(self) -> None:
        try:
            self.camera_manager.stop_camera()
            self.image_preview.set_camera_active(False)
            self.status_bar.update_status("Camera stopped")
            logger.info("Camera stopped")
        except Exception as e:
            logger.error("Failed to stop camera: %s", e)

    def toggle_camera(self) -> None:
        if self.camera_manager.is_camera_active():
            self.stop_camera()
        else:
            self.start_camera()

    def save_config(self) -> None:
        try:
            filepath = self.config_manager.save_threshold_config(
                self.current_threshold,
                description="User saved threshold config",
            )
            self.status_bar.update_status(f"Config saved: {filepath}")
            messagebox.showinfo("Success", f"Config saved to: {filepath}")
            logger.info("Config saved: %s", filepath)
        except Exception as e:
            logger.error("Failed to save config: %s", e)
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def load_config(self) -> None:
        file_types = [("JSON config", "*.json"), ("All files", "*.*")]
        filename = filedialog.askopenfilename(title="Select config file", filetypes=file_types)
        if not filename:
            return

        try:
            config_data = self.config_manager.load_threshold_config(filename)
            threshold = config_data["threshold"]
            self.current_threshold = threshold
            self.hsv_control.update_threshold(threshold)
            self.process_current_image()

            self.status_bar.update_status(f"Config loaded: {filename}")
            messagebox.showinfo("Success", f"Loaded config: {config_data.get('name', 'unnamed')}")
            logger.info("Config loaded: %s", filename)
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            messagebox.showerror("Error", f"Failed to load config: {e}")

    def export_config(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Export config",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not filename:
            return

        try:
            self.config_manager.export_config(
                self.current_threshold,
                filename,
                description="Exported threshold config",
            )
            self.status_bar.update_status(f"Config exported: {filename}")
            messagebox.showinfo("Success", f"Config exported to: {filename}")
            logger.info("Config exported: %s", filename)
        except Exception as e:
            logger.error("Failed to export config: %s", e)
            messagebox.showerror("Error", f"Failed to export config: {e}")

    def reset_threshold(self) -> None:
        try:
            default_threshold = self.config_manager.reset_to_defaults()
            self.current_threshold = default_threshold
            self.hsv_control.update_threshold(default_threshold)
            self.process_current_image()
            self.status_bar.update_status("Threshold reset to default")
            logger.info("Threshold reset")
        except Exception as e:
            logger.error("Failed to reset threshold: %s", e)

    def show_camera_settings(self) -> None:
        messagebox.showinfo("Notice", "Camera settings are under development")

    def show_color_presets(self) -> None:
        messagebox.showinfo("Notice", "Color presets dialog is under development")

    def show_help(self) -> None:
        help_text = (
            "ColorEdit usage:\n\n"
            "1. Input source\n"
            "   - File > Open Image to load local image\n"
            "   - Camera > Start Camera for live preview\n\n"
            "2. HSV tuning\n"
            "   - Adjust H(0-179), S(0-255), V(0-255) ranges\n"
            "   - Both min and max are editable with sliders/spinboxes\n\n"
            "3. Config management\n"
            "   - Ctrl+S save config, Ctrl+L load config\n"
            "   - Export config to any target path\n\n"
            "4. Shortcuts\n"
            "   - Space: start/stop camera\n"
            "   - F5: refresh processing\n"
            "   - Ctrl+Q: quit"
        )
        messagebox.showinfo("Usage", help_text)

    def show_about(self) -> None:
        about_text = (
            "ColorEdit v1.0.0\n\n"
            "Visual HSV threshold editor with live camera/image mask preview.\n\n"
            "Built with Python + OpenCV + Tkinter"
        )
        messagebox.showinfo("About", about_text)

    def update_displays(self) -> None:
        if self.current_image is not None:
            self.process_current_image()

    def on_window_close(self) -> None:
        try:
            if self.camera_manager.is_camera_active():
                self.camera_manager.stop_camera()
            logger.info("Application closing")
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            logger.error("Error while closing application: %s", e)
            self.root.destroy()
