#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HSV control panel."""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Tuple, Callable
import colorsys

logger = logging.getLogger(__name__)


class HSVControlPanel:
    """Panel for HSV threshold controls."""

    def __init__(
        self,
        parent: tk.Widget,
        initial_threshold: Dict[str, Tuple[int, int]],
        on_threshold_changed: Callable[[Dict[str, Tuple[int, int]]], None],
    ):
        self.parent = parent
        self.threshold = initial_threshold.copy()
        self.on_threshold_changed = on_threshold_changed

        self.setup_ui()
        self.update_threshold(initial_threshold)
        logger.debug("HSV control panel initialized")

    def setup_ui(self) -> None:
        self.main_frame = ttk.Frame(self.parent, style="Panel.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.main_frame.columnconfigure(0, weight=1)

        self.create_channel_control("Hue (H)", "h", 0, 179, 0)
        self.create_channel_control("Saturation (S)", "s", 0, 255, 1)
        self.create_channel_control("Value (V)", "v", 0, 255, 2)

        self.create_preset_buttons()
        self.create_action_buttons()

    def create_channel_control(self, label: str, channel: str, min_val: int, max_val: int, row: int) -> None:
        channel_frame = ttk.LabelFrame(self.main_frame, text=label, padding=10, style="Card.TLabelframe")
        channel_frame.grid(row=row, column=0, sticky="ew", padx=2, pady=4)
        channel_frame.columnconfigure(0, weight=1)

        values_frame = ttk.Frame(channel_frame, style="Panel.TFrame")
        values_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(values_frame, text="Min").grid(row=0, column=0, sticky="w")
        min_var = tk.IntVar(value=self.threshold[channel][0])
        min_spinbox = ttk.Spinbox(
            values_frame,
            from_=min_val,
            to=max_val,
            width=6,
            textvariable=min_var,
            command=lambda: self.on_value_changed(channel, 0, min_var.get()),
        )
        min_spinbox.grid(row=0, column=1, padx=(6, 14), sticky="w")
        min_spinbox.bind("<Return>", lambda _e: self.on_value_changed(channel, 0, min_var.get()))
        min_spinbox.bind("<FocusOut>", lambda _e: self.on_value_changed(channel, 0, min_var.get()))

        ttk.Label(values_frame, text="Max").grid(row=0, column=2, sticky="w")
        max_var = tk.IntVar(value=self.threshold[channel][1])
        max_spinbox = ttk.Spinbox(
            values_frame,
            from_=min_val,
            to=max_val,
            width=6,
            textvariable=max_var,
            command=lambda: self.on_value_changed(channel, 1, max_var.get()),
        )
        max_spinbox.grid(row=0, column=3, padx=(6, 12), sticky="w")
        max_spinbox.bind("<Return>", lambda _e: self.on_value_changed(channel, 1, max_var.get()))
        max_spinbox.bind("<FocusOut>", lambda _e: self.on_value_changed(channel, 1, max_var.get()))

        range_var = tk.StringVar(value=f"{self.threshold[channel][0]} - {self.threshold[channel][1]}")
        ttk.Label(values_frame, textvariable=range_var, style="Subtle.TLabel").grid(row=0, column=4, sticky="e")
        values_frame.columnconfigure(4, weight=1)

        slider_frame = ttk.Frame(channel_frame, style="Panel.TFrame")
        slider_frame.pack(fill=tk.X)

        min_slider = ttk.Scale(
            slider_frame,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            variable=min_var,
            command=lambda v: self.on_slider_changed(channel, 0, int(float(v))),
        )
        min_slider.pack(fill=tk.X, pady=(0, 2))

        max_slider = ttk.Scale(
            slider_frame,
            from_=min_val,
            to=max_val,
            orient=tk.HORIZONTAL,
            variable=max_var,
            command=lambda v: self.on_slider_changed(channel, 1, int(float(v))),
        )
        max_slider.pack(fill=tk.X)

        if channel == "h":
            self.create_hue_preview(channel_frame)
        else:
            preview = tk.Canvas(channel_frame, height=8, highlightthickness=0, bd=0, bg="#24375f")
            preview.pack(fill=tk.X, pady=(8, 0))

        setattr(self, f"{channel}_min_var", min_var)
        setattr(self, f"{channel}_max_var", max_var)
        setattr(self, f"{channel}_min_slider", min_slider)
        setattr(self, f"{channel}_max_slider", max_slider)
        setattr(self, f"{channel}_range_var", range_var)

    def create_hue_preview(self, parent: tk.Widget) -> None:
        canvas = tk.Canvas(parent, height=10, bg="#0b111f", highlightthickness=0, bd=0)
        canvas.pack(fill=tk.X, pady=(8, 0))
        self.h_preview_canvas = canvas
        canvas.bind("<Configure>", self.on_hue_canvas_configure)

    def create_preset_buttons(self) -> None:
        preset_frame = ttk.LabelFrame(self.main_frame, text="Quick Presets", padding=10, style="Card.TLabelframe")
        preset_frame.grid(row=3, column=0, sticky="ew", padx=2, pady=4)

        presets = [
            ("Red", {"h": (0, 10), "s": (100, 255), "v": (50, 255)}),
            ("Green", {"h": (40, 70), "s": (100, 255), "v": (50, 255)}),
            ("Blue", {"h": (100, 130), "s": (100, 255), "v": (50, 255)}),
            ("Yellow", {"h": (20, 30), "s": (100, 255), "v": (100, 255)}),
        ]

        for i, (name, threshold) in enumerate(presets):
            ttk.Button(preset_frame, text=name, command=lambda t=threshold: self.apply_preset(t)).grid(
                row=i // 2,
                column=i % 2,
                padx=3,
                pady=3,
                sticky="ew",
            )

        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)

    def create_action_buttons(self) -> None:
        action_frame = ttk.LabelFrame(self.main_frame, text="Actions", padding=10, style="Card.TLabelframe")
        action_frame.grid(row=4, column=0, sticky="ew", padx=2, pady=4)

        ttk.Button(action_frame, text="Reset", command=self.reset_threshold).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(action_frame, text="Invert", command=self.invert_threshold).pack(side=tk.LEFT, padx=6)
        ttk.Button(action_frame, text="Fine Tune", command=self.show_fine_tune).pack(side=tk.LEFT, padx=6)

    def on_value_changed(self, channel: str, index: int, value: int) -> None:
        try:
            value = max(0, min(179 if channel == "h" else 255, value))

            current_values = list(self.threshold[channel])
            current_values[index] = value

            if index == 0 and current_values[0] > current_values[1]:
                current_values[1] = current_values[0]
            elif index == 1 and current_values[1] < current_values[0]:
                current_values[0] = current_values[1]

            self.threshold[channel] = tuple(current_values)

            getattr(self, f"{channel}_min_var").set(self.threshold[channel][0])
            getattr(self, f"{channel}_max_var").set(self.threshold[channel][1])
            getattr(self, f"{channel}_range_var").set(f"{self.threshold[channel][0]} - {self.threshold[channel][1]}")

            self.on_threshold_changed(self.threshold.copy())
        except Exception as e:
            logger.error("Failed to handle value change: %s", e)

    def on_slider_changed(self, channel: str, index: int, value: int) -> None:
        self.on_value_changed(channel, index, value)

    def on_hue_canvas_configure(self, event) -> None:
        try:
            canvas = event.widget
            canvas.delete("all")

            width = canvas.winfo_width()
            if width > 1:
                for i in range(width):
                    hue = int(i * 179 / width)
                    color = self.hsv_to_hex(hue, 255, 255)
                    canvas.create_line(i, 0, i, 12, fill=color, width=1)
        except Exception as e:
            logger.error("Failed to refresh hue preview: %s", e)

    def hsv_to_hex(self, h: int, s: int, v: int) -> str:
        h_norm = h / 179.0
        s_norm = s / 255.0
        v_norm = v / 255.0
        r, g, b = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def apply_preset(self, preset_threshold: Dict[str, Tuple[int, int]]) -> None:
        try:
            self.update_threshold(preset_threshold)
            self.on_threshold_changed(self.threshold.copy())
            logger.info("Preset applied")
        except Exception as e:
            logger.error("Failed to apply preset: %s", e)

    def reset_threshold(self) -> None:
        default_threshold = {"h": (0, 179), "s": (0, 255), "v": (0, 255)}
        self.update_threshold(default_threshold)
        self.on_threshold_changed(self.threshold.copy())
        logger.info("Threshold reset")

    def invert_threshold(self) -> None:
        try:
            inverted = {}
            for channel, (min_val, max_val) in self.threshold.items():
                if channel == "h":
                    mid = (min_val + max_val) // 2
                    new_min = (mid + 90) % 180
                    new_max = (mid - 90) % 180
                    if new_min > new_max:
                        new_min, new_max = new_max, new_min
                    inverted[channel] = (new_min, new_max)
                else:
                    inverted[channel] = (255 - max_val, 255 - min_val)

            self.update_threshold(inverted)
            self.on_threshold_changed(self.threshold.copy())
            logger.info("Threshold inverted")
        except Exception as e:
            logger.error("Failed to invert threshold: %s", e)

    def show_fine_tune(self) -> None:
        from tkinter import messagebox

        messagebox.showinfo("Notice", "Fine tune dialog is under development")

    def update_threshold(self, threshold: Dict[str, Tuple[int, int]]) -> None:
        try:
            self.threshold = threshold.copy()
            for channel in ["h", "s", "v"]:
                min_val, max_val = self.threshold[channel]
                getattr(self, f"{channel}_min_var").set(min_val)
                getattr(self, f"{channel}_max_var").set(max_val)
                getattr(self, f"{channel}_range_var").set(f"{min_val} - {max_val}")
            logger.debug("Threshold display updated: %s", threshold)
        except Exception as e:
            logger.error("Failed to update threshold display: %s", e)

    def get_threshold(self) -> Dict[str, Tuple[int, int]]:
        return self.threshold.copy()
