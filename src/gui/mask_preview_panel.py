#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mask preview and histogram panel."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MaskPreviewPanel:
    """Panel for mask display, histogram, and statistics."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent

        self.current_mask = None
        self.current_histogram = None
        self.current_statistics = None

        self.setup_ui()
        logger.debug("Mask preview panel initialized")

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.parent, style="Panel.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.mask_frame = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.histogram_frame = ttk.Frame(self.notebook, style="Panel.TFrame")
        self.notebook.add(self.mask_frame, text="Mask")
        self.notebook.add(self.histogram_frame, text="Histogram")

        self.create_mask_display()
        self.create_histogram_display()
        self.create_statistics_display()

    def create_mask_display(self) -> None:
        self.mask_canvas = tk.Canvas(
            self.mask_frame,
            bg="#0b111f",
            highlightthickness=1,
            highlightbackground="#24375f",
        )
        self.mask_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.mask_canvas.bind("<Configure>", self.on_mask_canvas_configure)
        self.show_mask_placeholder()

    def create_histogram_display(self) -> None:
        self.fig = Figure(figsize=(8, 6), dpi=80, facecolor="#0f1628")
        self.ax_h = self.fig.add_subplot(3, 1, 1)
        self.ax_s = self.fig.add_subplot(3, 1, 2)
        self.ax_v = self.fig.add_subplot(3, 1, 3)

        for ax in [self.ax_h, self.ax_s, self.ax_v]:
            ax.set_facecolor("#151f37")
            ax.tick_params(colors="#a9b7dd", labelsize=8)
            ax.xaxis.label.set_color("#b6c4e6")
            ax.yaxis.label.set_color("#b6c4e6")
            ax.title.set_color("#dce7ff")

        self.histogram_canvas = FigureCanvasTkAgg(self.fig, self.histogram_frame)
        self.histogram_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.update_histogram_display()

    def create_statistics_display(self) -> None:
        stats_frame = ttk.LabelFrame(self.main_frame, text="Statistics", padding=10, style="Card.TLabelframe")
        stats_frame.pack(fill=tk.X)

        info_frame = ttk.Frame(stats_frame, style="Panel.TFrame")
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="Pixels:").grid(row=0, column=0, sticky="w")
        self.pixel_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.pixel_count_var).grid(row=0, column=1, sticky="w", padx=(6, 16))

        ttk.Label(info_frame, text="Coverage:").grid(row=0, column=2, sticky="w")
        self.coverage_var = tk.StringVar(value="0.0%")
        ttk.Label(info_frame, textvariable=self.coverage_var).grid(row=0, column=3, sticky="w", padx=(6, 16))

        ttk.Label(info_frame, text="Contours:").grid(row=0, column=4, sticky="w")
        self.contour_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.contour_count_var).grid(row=0, column=5, sticky="w", padx=(6, 0))

        button_frame = ttk.Frame(stats_frame, style="Panel.TFrame")
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Export Mask", command=self.export_mask).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(button_frame, text="Save Histogram", command=self.save_histogram).pack(side=tk.LEFT, padx=6)
        ttk.Button(button_frame, text="Toggle View", command=self.toggle_view).pack(side=tk.LEFT, padx=6)

    def show_mask_placeholder(self) -> None:
        self.mask_canvas.delete("all")
        canvas_width = self.mask_canvas.winfo_width()
        canvas_height = self.mask_canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            self.mask_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="Mask preview will appear here",
                fill="#6e84b8",
                font=("Segoe UI", 11),
            )

    def update_mask(self, mask: np.ndarray) -> None:
        try:
            self.current_mask = mask
            self.display_mask_on_canvas()
        except Exception as e:
            logger.error("Failed to update mask display: %s", e)

    def display_mask_on_canvas(self) -> None:
        if self.current_mask is None:
            self.show_mask_placeholder()
            return

        try:
            canvas_width = self.mask_canvas.winfo_width()
            canvas_height = self.mask_canvas.winfo_height()
            if canvas_width <= 1 or canvas_height <= 1:
                return

            mask_resized = self.resize_mask_for_display(self.current_mask, canvas_width, canvas_height)
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_TURBO)
            mask_rgb = cv2.cvtColor(mask_colored, cv2.COLOR_BGR2RGB)

            pil_image = Image.fromarray(mask_rgb)
            tk_image = ImageTk.PhotoImage(pil_image)

            self.mask_canvas.delete("all")
            img_width, img_height = pil_image.size
            x = (canvas_width - img_width) // 2
            y = (canvas_height - img_height) // 2
            self.mask_canvas.create_image(x, y, anchor=tk.NW, image=tk_image)
            self.mask_canvas.image = tk_image
        except Exception as e:
            logger.error("Failed to render mask: %s", e)

    def resize_mask_for_display(self, mask: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
        height, width = mask.shape[:2]
        scale_w = (max_width - 20) / width
        scale_h = (max_height - 20) / height
        scale = min(scale_w, scale_h, 1.0)

        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
        return mask

    def update_histogram(self, histogram: Dict[str, np.ndarray]) -> None:
        try:
            self.current_histogram = histogram
            self.update_histogram_display()
        except Exception as e:
            logger.error("Failed to update histogram: %s", e)

    def update_histogram_display(self) -> None:
        try:
            self.ax_h.clear()
            self.ax_s.clear()
            self.ax_v.clear()

            for ax in [self.ax_h, self.ax_s, self.ax_v]:
                ax.set_facecolor("#151f37")
                ax.tick_params(colors="#a9b7dd", labelsize=8)
                ax.xaxis.label.set_color("#b6c4e6")
                ax.yaxis.label.set_color("#b6c4e6")
                ax.title.set_color("#dce7ff")
                ax.grid(True, alpha=0.25, color="#2e416f")

            if self.current_histogram is None:
                self.ax_h.set_title("H (Hue) - No Data")
                self.ax_s.set_title("S (Saturation) - No Data")
                self.ax_v.set_title("V (Value) - No Data")
            else:
                h_data = self.current_histogram.get("h", [])
                if len(h_data) > 0:
                    self.ax_h.plot(h_data, color="#ff5f7a", linewidth=1.3)
                    self.ax_h.fill_between(range(len(h_data)), h_data, alpha=0.25, color="#ff5f7a")
                self.ax_h.set_title("H (Hue)")
                self.ax_h.set_xlabel("0-179")
                self.ax_h.set_ylabel("Frequency")

                s_data = self.current_histogram.get("s", [])
                if len(s_data) > 0:
                    self.ax_s.plot(s_data, color="#29e0a9", linewidth=1.3)
                    self.ax_s.fill_between(range(len(s_data)), s_data, alpha=0.25, color="#29e0a9")
                self.ax_s.set_title("S (Saturation)")
                self.ax_s.set_xlabel("0-255")
                self.ax_s.set_ylabel("Frequency")

                v_data = self.current_histogram.get("v", [])
                if len(v_data) > 0:
                    self.ax_v.plot(v_data, color="#12d6ff", linewidth=1.3)
                    self.ax_v.fill_between(range(len(v_data)), v_data, alpha=0.25, color="#12d6ff")
                self.ax_v.set_title("V (Value)")
                self.ax_v.set_xlabel("0-255")
                self.ax_v.set_ylabel("Frequency")

            self.fig.tight_layout(pad=1.1)
            self.histogram_canvas.draw()
        except Exception as e:
            logger.error("Failed to redraw histogram: %s", e)

    def update_statistics(self, statistics: Dict[str, Any]) -> None:
        try:
            self.current_statistics = statistics
            pixel_count = statistics.get("pixel_count", 0)
            coverage_ratio = statistics.get("coverage_ratio", 0.0)
            contour_count = statistics.get("contour_count", 0)

            self.pixel_count_var.set(f"{pixel_count:,}")
            self.coverage_var.set(f"{coverage_ratio:.2%}")
            self.contour_count_var.set(str(contour_count))
        except Exception as e:
            logger.error("Failed to update statistics: %s", e)

    def on_mask_canvas_configure(self, _event) -> None:
        if self.current_mask is not None:
            self.display_mask_on_canvas()
        else:
            self.show_mask_placeholder()

    def export_mask(self) -> None:
        if self.current_mask is None:
            messagebox.showwarning("Warning", "No mask to export")
            return

        try:
            filename = filedialog.asksaveasfilename(
                title="Export mask",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("All files", "*.*")],
            )
            if filename:
                cv2.imwrite(filename, self.current_mask)
                messagebox.showinfo("Success", f"Mask exported to: {filename}")
                logger.info("Mask exported: %s", filename)
        except Exception as e:
            logger.error("Failed to export mask: %s", e)
            messagebox.showerror("Error", f"Failed to export mask: {e}")

    def save_histogram(self) -> None:
        if self.current_histogram is None:
            messagebox.showwarning("Warning", "No histogram to save")
            return

        try:
            filename = filedialog.asksaveasfilename(
                title="Save histogram",
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")],
            )
            if filename:
                self.fig.savefig(filename, dpi=300, bbox_inches="tight", facecolor=self.fig.get_facecolor())
                messagebox.showinfo("Success", f"Histogram saved to: {filename}")
                logger.info("Histogram saved: %s", filename)
        except Exception as e:
            logger.error("Failed to save histogram: %s", e)
            messagebox.showerror("Error", f"Failed to save histogram: {e}")

    def toggle_view(self) -> None:
        current_tab = self.notebook.index(self.notebook.select())
        next_tab = (current_tab + 1) % self.notebook.index("end")
        self.notebook.select(next_tab)

    def clear_displays(self) -> None:
        self.current_mask = None
        self.current_histogram = None
        self.current_statistics = None
        self.show_mask_placeholder()
        self.update_histogram_display()
        self.update_statistics({"pixel_count": 0, "coverage_ratio": 0.0, "contour_count": 0})
