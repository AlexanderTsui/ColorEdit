#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Application status bar."""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class StatusBar:
    """Bottom status bar."""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.status_text = "Ready"
        self.progress_value = 0
        self.fps_count = 0
        self.memory_usage = 0.0
        self.clock_running = True

        self.setup_ui()
        self.start_clock_update()
        logger.debug("Status bar initialized")

    def setup_ui(self) -> None:
        self.status_frame = ttk.Frame(self.parent, style="Toolbar.TFrame")
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.create_status_widgets()

    def create_status_widgets(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.status_frame, textvariable=self.status_var, style="Subtle.TLabel").pack(side=tk.LEFT, padx=(10, 14), pady=6)

        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        progress_frame = ttk.Frame(self.status_frame, style="Toolbar.TFrame")
        progress_frame.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Label(progress_frame, text="Process", style="Subtle.TLabel").pack(side=tk.LEFT)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, length=90, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=(6, 5))

        self.progress_text_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_text_var, style="Subtle.TLabel", width=4).pack(side=tk.LEFT)

        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        fps_frame = ttk.Frame(self.status_frame, style="Toolbar.TFrame")
        fps_frame.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(fps_frame, text="FPS", style="Subtle.TLabel").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="0")
        ttk.Label(fps_frame, textvariable=self.fps_var).pack(side=tk.LEFT, padx=(6, 0))

        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        memory_frame = ttk.Frame(self.status_frame, style="Toolbar.TFrame")
        memory_frame.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(memory_frame, text="Memory", style="Subtle.TLabel").pack(side=tk.LEFT)
        self.memory_var = tk.StringVar(value="0 MB")
        ttk.Label(memory_frame, textvariable=self.memory_var).pack(side=tk.LEFT, padx=(6, 0))

        self.time_var = tk.StringVar(value=datetime.now().strftime("%H:%M:%S"))
        ttk.Label(self.status_frame, textvariable=self.time_var, style="Subtle.TLabel").pack(side=tk.RIGHT, padx=(0, 10))

        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Label(self.status_frame, textvariable=self.date_var, style="Subtle.TLabel").pack(side=tk.RIGHT, padx=(0, 8))

    def update_status(self, status: str) -> None:
        try:
            self.status_text = status
            self.status_var.set(status)
        except Exception as e:
            logger.error("Failed to update status: %s", e)

    def update_progress(self, value: int, text: Optional[str] = None) -> None:
        try:
            value = max(0, min(100, value))
            self.progress_value = value
            self.progress_var.set(value)
            self.progress_text_var.set(text if text is not None else f"{value}%")
        except Exception as e:
            logger.error("Failed to update progress: %s", e)

    def update_fps(self, fps: int) -> None:
        try:
            self.fps_count = fps
            self.fps_var.set(str(fps))
        except Exception as e:
            logger.error("Failed to update FPS: %s", e)

    def update_memory(self, memory_mb: float) -> None:
        try:
            self.memory_usage = memory_mb
            self.memory_var.set(f"{memory_mb:.1f} MB" if memory_mb < 1024 else f"{memory_mb / 1024:.1f} GB")
        except Exception as e:
            logger.error("Failed to update memory display: %s", e)

    def start_clock_update(self) -> None:
        def tick() -> None:
            if not self.clock_running:
                return
            try:
                now = datetime.now()
                self.time_var.set(now.strftime("%H:%M:%S"))
                self.date_var.set(now.strftime("%Y-%m-%d"))
            except Exception as e:
                logger.error("Clock update failed: %s", e)
            self.parent.after(1000, tick)

        self.parent.after(1000, tick)

    def stop_clock_update(self) -> None:
        self.clock_running = False

    def show_progress(self, show: bool = True) -> None:
        try:
            if show:
                self.progress_bar.pack(side=tk.LEFT, padx=(6, 5))
            else:
                self.progress_bar.pack_forget()
        except Exception as e:
            logger.error("Failed to toggle progress bar: %s", e)

    def reset_progress(self) -> None:
        self.update_progress(0, "0%")

    def set_busy(self, busy: bool = True) -> None:
        try:
            if busy:
                self.update_status("Processing...")
                self.progress_bar.configure(mode="indeterminate")
                self.progress_bar.start()
                self.progress_text_var.set("...")
            else:
                self.progress_bar.stop()
                self.progress_bar.configure(mode="determinate")
                self.update_status("Ready")
                self.reset_progress()
        except Exception as e:
            logger.error("Failed to set busy state: %s", e)

    def get_current_memory_usage(self) -> float:
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 50.0
        except Exception as e:
            logger.error("Failed to get memory usage: %s", e)
            return 0.0

    def auto_update_memory(self, interval: int = 5) -> None:
        def tick_memory() -> None:
            if not self.clock_running:
                return
            try:
                self.update_memory(self.get_current_memory_usage())
            except Exception as e:
                logger.error("Auto memory update failed: %s", e)
            self.parent.after(max(1, interval) * 1000, tick_memory)

        self.parent.after(max(1, interval) * 1000, tick_memory)

    def update_all(
        self,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        fps: Optional[int] = None,
        memory: Optional[float] = None,
    ) -> None:
        try:
            if status is not None:
                self.update_status(status)
            if progress is not None:
                self.update_progress(progress)
            if fps is not None:
                self.update_fps(fps)
            if memory is not None:
                self.update_memory(memory)
        except Exception as e:
            logger.error("Failed to update status bar: %s", e)

    def clear_all(self) -> None:
        self.update_status("Ready")
        self.reset_progress()
        self.update_fps(0)
        self.update_memory(0)

    def __del__(self):
        self.stop_clock_update()
