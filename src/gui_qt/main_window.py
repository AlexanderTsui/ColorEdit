#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qt main window for ColorEdit."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QImage, QKeySequence, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.camera_manager import CameraManager
from src.core.config_manager import ConfigManager
from src.core.image_processor import ImageProcessor

Threshold = Dict[str, Tuple[int, int]]


class PreviewLabel(QLabel):
    """QLabel that keeps image ratio on resize."""

    def __init__(self, min_height: int = 260):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(min_height)
        self.setFrameShape(QFrame.StyledPanel)
        self.setObjectName("previewLabel")
        self._image: Optional[QImage] = None

    def set_cv_image(self, image: np.ndarray, rgb: bool = False) -> None:
        if image is None:
            self.clear()
            self._image = None
            return

        if not rgb:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        h, w, ch = image.shape
        bytes_per_line = ch * w
        qimg = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
        self._image = qimg
        self._refresh_pixmap()

    def set_qimage(self, image: QImage) -> None:
        self._image = image
        self._refresh_pixmap()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh_pixmap()

    def _refresh_pixmap(self) -> None:
        if self._image is None:
            return
        scaled = QPixmap.fromImage(self._image).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)


class SakuraLayer(QWidget):
    """Lightweight sakura animation overlay."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.petals: list[Dict[str, float]] = []
        self.max_petals = 24
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(40)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.setGeometry(self.parentWidget().rect())
        if not self.petals and self.width() > 0:
            self._spawn_initial()

    def _spawn_initial(self) -> None:
        self.petals.clear()
        for _ in range(self.max_petals):
            self.petals.append(
                {
                    "x": random.uniform(0, max(1, self.width())),
                    "y": random.uniform(0, max(1, self.height())),
                    "size": random.uniform(8, 18),
                    "speed": random.uniform(0.7, 1.6),
                    "drift": random.uniform(-0.5, 0.5),
                    "phase": random.uniform(0.0, 6.0),
                }
            )

    def _tick(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return

        if len(self.petals) < self.max_petals:
            self.petals.append(
                {
                    "x": random.uniform(0, self.width()),
                    "y": -20.0,
                    "size": random.uniform(8, 18),
                    "speed": random.uniform(0.7, 1.6),
                    "drift": random.uniform(-0.5, 0.5),
                    "phase": random.uniform(0.0, 6.0),
                }
            )

        for petal in self.petals:
            petal["phase"] += 0.06
            petal["x"] += petal["drift"] + np.sin(petal["phase"]) * 0.4
            petal["y"] += petal["speed"]
            if petal["y"] > self.height() + 30:
                petal["y"] = -20.0
                petal["x"] = random.uniform(0, self.width())

        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        outline = QPen(QColor(255, 182, 193, 110), 1)

        for petal in self.petals:
            x = petal["x"]
            y = petal["y"]
            size = petal["size"]
            painter.setPen(outline)
            painter.setBrush(QColor(255, 209, 220, 95))
            painter.drawEllipse(QPointF(x, y), size * 0.52, size * 0.34)
            painter.drawEllipse(QPointF(x + size * 0.18, y + size * 0.1), size * 0.35, size * 0.24)


class ColorEditMainWindow(QMainWindow):
    """Main Qt window."""

    frame_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self.image_processor = ImageProcessor()
        self.config_manager = ConfigManager()
        self.config_manager.load_presets()
        self.camera_manager = CameraManager(self._on_camera_frame)

        self.current_image: Optional[np.ndarray] = None
        self.current_mask: Optional[np.ndarray] = None
        self.current_threshold: Threshold = self.config_manager.get_default_threshold()
        self.layout_mode = "triple"
        self.splitters: Dict[str, QSplitter] = {}
        self.ui_state_path = Path("configs") / "ui_state.json"

        self.frame_ready.connect(self._handle_camera_frame)

        self._setup_window()
        self._setup_actions()
        self._setup_ui()
        self._load_ui_state()
        self._build_layout(self.layout_mode)
        self._apply_theme()

    def _setup_window(self) -> None:
        self.setWindowTitle("ColorEdit - HSV Mask Editor")
        self.resize(1280, 840)
        self.setMinimumSize(980, 640)

    def _setup_actions(self) -> None:
        self.action_open = QAction("Open Image", self)
        self.action_open.setShortcut(QKeySequence("Ctrl+O"))
        self.action_open.triggered.connect(self.open_image_file)

        self.action_save = QAction("Save Config", self)
        self.action_save.setShortcut(QKeySequence("Ctrl+S"))
        self.action_save.triggered.connect(self.save_config)

        self.action_load = QAction("Load Config", self)
        self.action_load.setShortcut(QKeySequence("Ctrl+L"))
        self.action_load.triggered.connect(self.load_config)

        self.action_export = QAction("Export Config", self)
        self.action_export.triggered.connect(self.export_config)

        self.action_quit = QAction("Quit", self)
        self.action_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.action_quit.triggered.connect(self.close)

        self.action_cam_start = QAction("Start Camera", self)
        self.action_cam_start.triggered.connect(self.start_camera)

        self.action_cam_stop = QAction("Stop Camera", self)
        self.action_cam_stop.triggered.connect(self.stop_camera)

        self.action_reset = QAction("Reset Threshold", self)
        self.action_reset.triggered.connect(self.reset_threshold)

        self.action_invert = QAction("Invert Threshold", self)
        self.action_invert.triggered.connect(self.invert_threshold)

        self.action_refresh = QAction("Refresh", self)
        self.action_refresh.setShortcut(QKeySequence(Qt.Key_F5))
        self.action_refresh.triggered.connect(self.process_current_image)

        self.action_toggle_camera = QAction("Toggle Camera", self)
        self.action_toggle_camera.setShortcut(QKeySequence(Qt.Key_Space))
        self.action_toggle_camera.triggered.connect(self.toggle_camera)

        self.addAction(self.action_refresh)
        self.addAction(self.action_toggle_camera)

        menu_file = self.menuBar().addMenu("File")
        menu_file.addAction(self.action_open)
        menu_file.addSeparator()
        menu_file.addAction(self.action_save)
        menu_file.addAction(self.action_load)
        menu_file.addAction(self.action_export)
        menu_file.addSeparator()
        menu_file.addAction(self.action_quit)

        menu_camera = self.menuBar().addMenu("Camera")
        menu_camera.addAction(self.action_cam_start)
        menu_camera.addAction(self.action_cam_stop)

        menu_tools = self.menuBar().addMenu("Tools")
        menu_tools.addAction(self.action_reset)
        menu_tools.addAction(self.action_invert)

    def _setup_ui(self) -> None:
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        top_bar = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_image_file)
        self.camera_btn = QPushButton("Start Camera")
        self.camera_btn.clicked.connect(self.toggle_camera)

        top_bar.addWidget(open_btn)
        top_bar.addWidget(self.camera_btn)
        top_bar.addStretch(1)

        top_bar.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItem("Three Columns", "triple")
        self.layout_combo.addItem("Top/Bottom", "stacked")
        self.layout_combo.currentIndexChanged.connect(self._on_layout_combo_changed)
        top_bar.addWidget(self.layout_combo)

        root_layout.addLayout(top_bar)

        self.content_host = QWidget()
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.content_host, 1)

        self.image_panel = self._build_image_panel()
        self.control_panel = self._build_control_panel()
        self.mask_panel = self._build_mask_panel()

        self.setCentralWidget(root)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready")
        self.coverage_label = QLabel("Coverage: 0.00%")
        self.contour_label = QLabel("Contours: 0")
        status.addWidget(self.status_label)
        status.addPermanentWidget(self.coverage_label)
        status.addPermanentWidget(self.contour_label)

        self.sakura_layer = SakuraLayer(root)
        self.sakura_layer.raise_()

    def _build_image_panel(self) -> QWidget:
        box = QGroupBox("Image Preview")
        layout = QVBoxLayout(box)

        self.image_preview_label = PreviewLabel(min_height=300)
        self.image_preview_label.setText("Load an image or start camera")
        layout.addWidget(self.image_preview_label, 1)

        self.image_info_label = QLabel("No source")
        layout.addWidget(self.image_info_label)
        return box

    def _build_control_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        wrap = QWidget()
        scroll.setWidget(wrap)
        main = QVBoxLayout(wrap)
        main.setSpacing(10)

        hsv_box = QGroupBox("HSV Threshold")
        hsv_layout = QGridLayout(hsv_box)

        self.controls: Dict[str, Dict[str, Any]] = {}
        channels = [("h", 179, "Hue"), ("s", 255, "Saturation"), ("v", 255, "Value")]

        for row, (channel, max_val, title) in enumerate(channels):
            group = QGroupBox(title)
            form = QFormLayout(group)

            min_slider = QSlider(Qt.Horizontal)
            min_slider.setRange(0, max_val)
            max_slider = QSlider(Qt.Horizontal)
            max_slider.setRange(0, max_val)
            min_spin = QSpinBox()
            min_spin.setRange(0, max_val)
            max_spin = QSpinBox()
            max_spin.setRange(0, max_val)

            min_slider.valueChanged.connect(lambda v, c=channel: self._set_threshold_value(c, 0, v))
            max_slider.valueChanged.connect(lambda v, c=channel: self._set_threshold_value(c, 1, v))
            min_spin.valueChanged.connect(lambda v, c=channel: self._set_threshold_value(c, 0, v))
            max_spin.valueChanged.connect(lambda v, c=channel: self._set_threshold_value(c, 1, v))

            form.addRow("Min", min_slider)
            form.addRow("Min Value", min_spin)
            form.addRow("Max", max_slider)
            form.addRow("Max Value", max_spin)

            hsv_layout.addWidget(group, row, 0)
            self.controls[channel] = {
                "min_slider": min_slider,
                "max_slider": max_slider,
                "min_spin": min_spin,
                "max_spin": max_spin,
            }

        main.addWidget(hsv_box)

        preset_box = QGroupBox("Color Presets")
        preset_layout = QGridLayout(preset_box)
        presets = self.config_manager.get_color_presets()
        for i, (name, data) in enumerate(presets.items()):
            btn = QPushButton(name)
            threshold = {"h": tuple(data["h"]), "s": tuple(data["s"]), "v": tuple(data["v"])}
            btn.clicked.connect(lambda _=False, t=threshold: self.apply_threshold(t))
            preset_layout.addWidget(btn, i // 2, i % 2)
            if i >= 7:
                break
        main.addWidget(preset_box)

        action_box = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_box)
        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(self.reset_threshold)
        btn_invert = QPushButton("Invert")
        btn_invert.clicked.connect(self.invert_threshold)
        action_layout.addWidget(btn_reset)
        action_layout.addWidget(btn_invert)
        main.addWidget(action_box)

        main.addStretch(1)
        self._sync_controls()
        return scroll

    def _build_mask_panel(self) -> QWidget:
        box = QGroupBox("Mask Preview")
        layout = QVBoxLayout(box)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        mask_tab = QWidget()
        mask_layout = QVBoxLayout(mask_tab)
        self.mask_preview_label = PreviewLabel(min_height=260)
        self.mask_preview_label.setText("Mask output")
        mask_layout.addWidget(self.mask_preview_label)
        self.tabs.addTab(mask_tab, "Mask")

        hist_tab = QWidget()
        hist_layout = QVBoxLayout(hist_tab)
        self.figure = Figure(figsize=(5, 4), dpi=96)
        self.ax_h = self.figure.add_subplot(311)
        self.ax_s = self.figure.add_subplot(312)
        self.ax_v = self.figure.add_subplot(313)
        self.figure.tight_layout()
        self.hist_canvas = FigureCanvasQTAgg(self.figure)
        hist_layout.addWidget(self.hist_canvas)
        self.tabs.addTab(hist_tab, "Histogram")

        stats = QHBoxLayout()
        self.pixel_label = QLabel("Pixels: 0")
        self.coverage_value = QLabel("Coverage: 0.00%")
        self.contour_value = QLabel("Contours: 0")
        stats.addWidget(self.pixel_label)
        stats.addWidget(self.coverage_value)
        stats.addWidget(self.contour_value)
        stats.addStretch(1)
        layout.addLayout(stats)

        button_row = QHBoxLayout()
        export_mask_btn = QPushButton("Export Mask")
        export_mask_btn.clicked.connect(self.export_mask)
        save_hist_btn = QPushButton("Save Histogram")
        save_hist_btn.clicked.connect(self.save_histogram)
        toggle_btn = QPushButton("Toggle View")
        toggle_btn.clicked.connect(self.toggle_view)
        button_row.addWidget(export_mask_btn)
        button_row.addWidget(save_hist_btn)
        button_row.addWidget(toggle_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._update_histogram(None)
        return box

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff6fb, stop:1 #ffe5f1);
            }
            QGroupBox {
                border: 1px solid #f3a3c3;
                border-radius: 14px;
                margin-top: 10px;
                padding: 10px;
                background: rgba(255, 255, 255, 0.84);
                font-weight: 600;
            }
            QGroupBox::title {
                color: #a93c73;
                padding: 0 6px;
            }
            QPushButton {
                background: #ff7fad;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 7px 12px;
                font-weight: 600;
            }
            QPushButton:hover { background: #ff6ca1; }
            QPushButton:pressed { background: #eb4f8d; }
            QSlider::groove:horizontal {
                border-radius: 4px;
                height: 8px;
                background: #ffd3e4;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
                background: #ff4d94;
            }
            QLabel#previewLabel {
                border-radius: 12px;
                background: #fff9fc;
                color: #6b4860;
                border: 1px solid #ffc3dc;
            }
            QTabWidget::pane {
                border: 1px solid #ffc3dc;
                border-radius: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #ffd8e8;
                color: #7a395a;
                border-radius: 8px;
                padding: 7px 10px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #ff9fc2;
                color: white;
            }
            QStatusBar {
                background: rgba(255, 238, 246, 0.9);
                border-top: 1px solid #ffc8df;
            }
            """
        )

    def _build_layout(self, mode: str) -> None:
        self.layout_mode = mode

        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        for panel in (self.image_panel, self.control_panel, self.mask_panel):
            panel.setParent(None)

        self.splitters = {}

        if mode == "stacked":
            top = QSplitter(Qt.Horizontal)
            top.addWidget(self.image_panel)
            top.addWidget(self.mask_panel)
            top.setStretchFactor(0, 2)
            top.setStretchFactor(1, 2)

            main = QSplitter(Qt.Vertical)
            main.addWidget(top)
            main.addWidget(self.control_panel)
            main.setStretchFactor(0, 4)
            main.setStretchFactor(1, 2)

            self.content_layout.addWidget(main)
            self.splitters["main"] = main
            self.splitters["top"] = top
        else:
            main = QSplitter(Qt.Horizontal)
            main.addWidget(self.image_panel)
            main.addWidget(self.control_panel)
            main.addWidget(self.mask_panel)
            main.setStretchFactor(0, 4)
            main.setStretchFactor(1, 2)
            main.setStretchFactor(2, 4)
            self.content_layout.addWidget(main)
            self.splitters["main"] = main

        self._apply_saved_splitter_sizes()
        self._sync_layout_combo()

    def _sync_layout_combo(self) -> None:
        index = self.layout_combo.findData(self.layout_mode)
        if index >= 0:
            self.layout_combo.blockSignals(True)
            self.layout_combo.setCurrentIndex(index)
            self.layout_combo.blockSignals(False)

    def _on_layout_combo_changed(self, index: int) -> None:
        mode = self.layout_combo.itemData(index)
        if mode and mode != self.layout_mode:
            self._build_layout(mode)
            self._set_status(f"Layout changed: {self.layout_combo.currentText()}")

    def _set_threshold_value(self, channel: str, pos: int, value: int) -> None:
        min_val, max_val = self.current_threshold[channel]
        if pos == 0:
            min_val = min(value, max_val)
        else:
            max_val = max(value, min_val)
        self.current_threshold[channel] = (int(min_val), int(max_val))
        self._sync_controls(channel)
        self.process_current_image()

    def _sync_controls(self, only_channel: Optional[str] = None) -> None:
        channels = [only_channel] if only_channel else ["h", "s", "v"]
        for channel in channels:
            if channel is None:
                continue
            min_val, max_val = self.current_threshold[channel]
            control = self.controls[channel]
            for key, value in (
                ("min_slider", min_val),
                ("max_slider", max_val),
                ("min_spin", min_val),
                ("max_spin", max_val),
            ):
                widget = control[key]
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)

    def _on_camera_frame(self, frame: np.ndarray) -> None:
        self.frame_ready.emit(frame)

    def _handle_camera_frame(self, frame: np.ndarray) -> None:
        self.current_image = frame.copy()
        self.image_preview_label.set_cv_image(self.current_image)
        self.image_info_label.setText(f"Camera: {frame.shape[1]}x{frame.shape[0]}")
        self.process_current_image()
        info = self.camera_manager.get_camera_info()
        if info:
            self._set_status(f"Camera running - FPS: {info.get('current_fps', 0)}")

    def process_current_image(self) -> None:
        if self.current_image is None:
            return

        try:
            mask = self.image_processor.create_mask(self.current_image, self.current_threshold)
            self.current_mask = mask
            self._update_mask(mask)

            hsv = self.image_processor.convert_to_hsv(self.current_image)
            histogram = self.image_processor.calculate_histogram(hsv)
            self._update_histogram(histogram)

            stats = self.image_processor.get_mask_statistics(mask, self.current_image.shape[:2])
            self._update_statistics(stats)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Image processing failed: {exc}")

    def _update_mask(self, mask: np.ndarray) -> None:
        colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        self.mask_preview_label.set_cv_image(colored)

    def _update_histogram(self, histogram: Optional[Dict[str, np.ndarray]]) -> None:
        for ax in (self.ax_h, self.ax_s, self.ax_v):
            ax.clear()
            ax.grid(True, alpha=0.2)

        if histogram is None:
            self.ax_h.set_title("H channel")
            self.ax_s.set_title("S channel")
            self.ax_v.set_title("V channel")
        else:
            self.ax_h.plot(histogram.get("h", []), color="#ff4d94", linewidth=1.2)
            self.ax_h.set_title("H (0-179)")
            self.ax_s.plot(histogram.get("s", []), color="#ff6fa8", linewidth=1.2)
            self.ax_s.set_title("S (0-255)")
            self.ax_v.plot(histogram.get("v", []), color="#f29cbc", linewidth=1.2)
            self.ax_v.set_title("V (0-255)")

        self.hist_canvas.draw_idle()

    def _update_statistics(self, stats: Dict[str, Any]) -> None:
        pixels = int(stats.get("pixel_count", 0))
        coverage = float(stats.get("coverage_ratio", 0.0))
        contours = int(stats.get("contour_count", 0))

        self.pixel_label.setText(f"Pixels: {pixels:,}")
        self.coverage_value.setText(f"Coverage: {coverage:.2%}")
        self.contour_value.setText(f"Contours: {contours}")

        self.coverage_label.setText(f"Coverage: {coverage:.2%}")
        self.contour_label.setText(f"Contours: {contours}")

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def open_image_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff)",
        )
        if not file_path:
            return

        if self.camera_manager.is_camera_active():
            self.stop_camera()

        image = cv2.imread(file_path)
        if image is None:
            QMessageBox.warning(self, "Warning", "Unable to read image")
            return

        image = self.image_processor.resize_image(image)
        self.current_image = image
        self.image_preview_label.set_cv_image(image)
        self.image_info_label.setText(f"Image: {image.shape[1]}x{image.shape[0]} - {Path(file_path).name}")
        self.process_current_image()
        self._set_status(f"Loaded image: {Path(file_path).name}")

    def start_camera(self) -> None:
        if self.camera_manager.start_camera():
            self.camera_btn.setText("Stop Camera")
            self._set_status("Camera started")
        else:
            QMessageBox.critical(self, "Error", self.camera_manager.get_error_message())

    def stop_camera(self) -> None:
        self.camera_manager.stop_camera()
        self.camera_btn.setText("Start Camera")
        self._set_status("Camera stopped")

    def toggle_camera(self) -> None:
        if self.camera_manager.is_camera_active():
            self.stop_camera()
        else:
            self.start_camera()

    def save_config(self) -> None:
        try:
            saved = self.config_manager.save_threshold_config(
                self.current_threshold,
                description="Saved from Qt UI",
            )
            self._set_status(f"Config saved: {Path(saved).name}")
            QMessageBox.information(self, "Saved", f"Config saved to:\n{saved}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Save failed: {exc}")

    def load_config(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if not file_path:
            return

        try:
            data = self.config_manager.load_threshold_config(file_path)
            threshold = data["threshold"]
            self.current_threshold = {
                "h": tuple(threshold["h"]),
                "s": tuple(threshold["s"]),
                "v": tuple(threshold["v"]),
            }
            self._sync_controls()
            self.process_current_image()
            self._set_status(f"Config loaded: {Path(file_path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Load failed: {exc}")

    def export_config(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Config", "threshold.json", "JSON (*.json)")
        if not file_path:
            return
        try:
            self.config_manager.export_config(self.current_threshold, file_path, description="Exported from Qt UI")
            self._set_status(f"Config exported: {Path(file_path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Export failed: {exc}")

    def reset_threshold(self) -> None:
        self.current_threshold = self.config_manager.reset_to_defaults()
        self._sync_controls()
        self.process_current_image()
        self._set_status("Threshold reset")

    def invert_threshold(self) -> None:
        inverted: Threshold = {}
        for channel, (min_val, max_val) in self.current_threshold.items():
            if channel == "h":
                mid = (min_val + max_val) // 2
                new_min = (mid + 90) % 180
                new_max = (mid - 90) % 180
                if new_min > new_max:
                    new_min, new_max = new_max, new_min
                inverted[channel] = (int(new_min), int(new_max))
            else:
                inverted[channel] = (255 - max_val, 255 - min_val)

        self.current_threshold = inverted
        self._sync_controls()
        self.process_current_image()
        self._set_status("Threshold inverted")

    def apply_threshold(self, threshold: Threshold) -> None:
        self.current_threshold = threshold
        self._sync_controls()
        self.process_current_image()
        self._set_status("Preset applied")

    def export_mask(self) -> None:
        if self.current_mask is None:
            QMessageBox.information(self, "Info", "No mask available")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Mask",
            "mask.png",
            "PNG (*.png);;JPEG (*.jpg)",
        )
        if not file_path:
            return
        cv2.imwrite(file_path, self.current_mask)
        self._set_status(f"Mask exported: {Path(file_path).name}")

    def save_histogram(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Histogram",
            "histogram.png",
            "PNG (*.png);;PDF (*.pdf)",
        )
        if not file_path:
            return
        self.figure.savefig(file_path, dpi=220, bbox_inches="tight")
        self._set_status(f"Histogram saved: {Path(file_path).name}")

    def toggle_view(self) -> None:
        index = self.tabs.currentIndex()
        self.tabs.setCurrentIndex((index + 1) % self.tabs.count())

    def _load_ui_state(self) -> None:
        if not self.ui_state_path.exists():
            return

        try:
            data = json.loads(self.ui_state_path.read_text(encoding="utf-8"))
        except Exception:
            return

        mode = data.get("layout_mode")
        if mode in {"triple", "stacked"}:
            self.layout_mode = mode

        self.saved_splitter_sizes = data.get("splitter_sizes", {})

    def _apply_saved_splitter_sizes(self) -> None:
        saved = getattr(self, "saved_splitter_sizes", {})
        if not saved:
            return

        QApplication.processEvents()
        for name, splitter in self.splitters.items():
            values = saved.get(name)
            if values and len(values) == splitter.count():
                splitter.setSizes([int(v) for v in values])

    def _save_ui_state(self) -> None:
        self.ui_state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "layout_mode": self.layout_mode,
            "splitter_sizes": {name: splitter.sizes() for name, splitter in self.splitters.items()},
        }
        self.ui_state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def closeEvent(self, event) -> None:  # noqa: N802
        self.stop_camera()
        self._save_ui_state()
        event.accept()
