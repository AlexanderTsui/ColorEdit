#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掩码预览面板模块
实现掩码图像显示和直方图可视化
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MaskPreviewPanel:
    """掩码预览面板类"""
    
    def __init__(self, parent: tk.Widget):
        """
        初始化掩码预览面板
        
        Args:
            parent: 父容器
        """
        self.parent = parent
        
        # 当前数据
        self.current_mask = None
        self.current_histogram = None
        self.current_statistics = None
        
        # 显示状态
        self.show_histogram = True
        
        # 创建界面
        self.setup_ui()
        
        logger.debug("掩码预览面板初始化完成")
    
    def setup_ui(self) -> None:
        """设置用户界面"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 掩码显示标签页
        self.mask_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.mask_frame, text="Mask")
        
        # 直方图标签页
        self.histogram_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.histogram_frame, text="Histogram")
        
        # 创建掩码显示区域
        self.create_mask_display()
        
        # 创建直方图显示区域
        self.create_histogram_display()
        
        # 创建统计信息区域
        self.create_statistics_display()
    
    def create_mask_display(self) -> None:
        """创建掩码显示区域"""
        # 掩码画布
        self.mask_canvas = tk.Canvas(self.mask_frame, bg='gray20', highlightthickness=0)
        self.mask_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定画布配置事件
        self.mask_canvas.bind('<Configure>', self.on_mask_canvas_configure)
        
        # 显示初始提示
        self.show_mask_placeholder()
    
    def create_histogram_display(self) -> None:
        """创建直方图显示区域"""
        # 创建matplotlib图形
        self.fig = Figure(figsize=(8, 6), dpi=80, facecolor='white')
        self.fig.suptitle('HSV Histogram', fontsize=14, fontweight='bold')
        
        # 创建子图
        self.ax_h = self.fig.add_subplot(3, 1, 1)
        self.ax_s = self.fig.add_subplot(3, 1, 2)
        self.ax_v = self.fig.add_subplot(3, 1, 3)
        
        # 设置子图标题和标签
        self.ax_h.set_title('H (Hue)', fontsize=10)
        self.ax_h.set_xlabel('Hue Value (0-179)')
        self.ax_h.set_ylabel('Frequency')
        
        self.ax_s.set_title('S (Saturation)', fontsize=10)
        self.ax_s.set_xlabel('Saturation Value (0-255)')
        self.ax_s.set_ylabel('Frequency')
        
        self.ax_v.set_title('V (Value)', fontsize=10)
        self.ax_v.set_xlabel('Value (0-255)')
        self.ax_v.set_ylabel('Frequency')
        
        # 调整布局
        self.fig.tight_layout()
        
        # 创建tkinter画布
        self.histogram_canvas = FigureCanvasTkAgg(self.fig, self.histogram_frame)
        self.histogram_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化空直方图
        self.update_histogram_display()
    
    def create_statistics_display(self) -> None:
        """创建统计信息显示区域"""
        # 统计信息框架（在主框架底部）
        stats_frame = ttk.LabelFrame(self.main_frame, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # 创建统计信息显示
        info_frame = ttk.Frame(stats_frame)
        info_frame.pack(fill=tk.X)
        
        # 像素数量
        ttk.Label(info_frame, text="Pixels:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.pixel_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.pixel_count_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(0, 20))
        
        # 覆盖率
        ttk.Label(info_frame, text="Coverage:").grid(row=0, column=2, sticky="w", padx=(0, 5))
        self.coverage_var = tk.StringVar(value="0.0%")
        ttk.Label(info_frame, textvariable=self.coverage_var, font=("Arial", 10, "bold")).grid(row=0, column=3, sticky="w", padx=(0, 20))
        
        # 轮廓数量
        ttk.Label(info_frame, text="Contours:").grid(row=0, column=4, sticky="w", padx=(0, 5))
        self.contour_count_var = tk.StringVar(value="0")
        ttk.Label(info_frame, textvariable=self.contour_count_var, font=("Arial", 10, "bold")).grid(row=0, column=5, sticky="w")
        
        # 操作按钮框架
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 导出掩码按钮
        export_btn = ttk.Button(button_frame, text="Export Mask", command=self.export_mask)
        export_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 保存直方图按钮
        save_hist_btn = ttk.Button(button_frame, text="Save Histogram", command=self.save_histogram)
        save_hist_btn.pack(side=tk.LEFT, padx=5)
        
        # 切换显示按钮
        toggle_btn = ttk.Button(button_frame, text="Toggle View", command=self.toggle_view)
        toggle_btn.pack(side=tk.LEFT, padx=5)
    
    def show_mask_placeholder(self) -> None:
        """显示掩码占位符"""
        self.mask_canvas.delete("all")
        
        canvas_width = self.mask_canvas.winfo_width()
        canvas_height = self.mask_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            
            self.mask_canvas.create_text(center_x, center_y, 
                                       text="Mask will be displayed here", 
                                       fill="gray50", font=("Arial", 12))
    
    def update_mask(self, mask: np.ndarray) -> None:
        """
        更新掩码显示
        
        Args:
            mask: 掩码图像
        """
        try:
            self.current_mask = mask
            self.display_mask_on_canvas()
            
        except Exception as e:
            logger.error(f"更新掩码显示失败: {e}")
    
    def display_mask_on_canvas(self) -> None:
        """在画布上显示掩码"""
        if self.current_mask is None:
            self.show_mask_placeholder()
            return
        
        try:
            # 获取画布尺寸
            canvas_width = self.mask_canvas.winfo_width()
            canvas_height = self.mask_canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                return
            
            # 调整掩码大小以适应画布
            mask_resized = self.resize_mask_for_display(self.current_mask, canvas_width, canvas_height)
            
            # 转换为彩色图像用于显示
            mask_colored = cv2.applyColorMap(mask_resized, cv2.COLORMAP_JET)
            mask_rgb = cv2.cvtColor(mask_colored, cv2.COLOR_BGR2RGB)
            
            # 转换为PIL图像
            pil_image = Image.fromarray(mask_rgb)
            
            # 转换为Tkinter图像
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # 清空画布并显示图像
            self.mask_canvas.delete("all")
            
            # 计算居中位置
            img_width, img_height = pil_image.size
            x = (canvas_width - img_width) // 2
            y = (canvas_height - img_height) // 2
            
            self.mask_canvas.create_image(x, y, anchor=tk.NW, image=tk_image)
            
            # 保存图像引用
            self.mask_canvas.image = tk_image
            
        except Exception as e:
            logger.error(f"显示掩码失败: {e}")
    
    def resize_mask_for_display(self, mask: np.ndarray, max_width: int, max_height: int) -> np.ndarray:
        """
        调整掩码大小以适应显示
        
        Args:
            mask: 原始掩码
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            调整大小后的掩码
        """
        height, width = mask.shape[:2]
        
        # 计算缩放比例
        scale_w = (max_width - 20) / width  # 留出边距
        scale_h = (max_height - 20) / height
        scale = min(scale_w, scale_h, 1.0)  # 不放大
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return cv2.resize(mask, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
        
        return mask
    
    def update_histogram(self, histogram: Dict[str, np.ndarray]) -> None:
        """
        更新直方图显示
        
        Args:
            histogram: 直方图数据
        """
        try:
            self.current_histogram = histogram
            self.update_histogram_display()
            
        except Exception as e:
            logger.error(f"更新直方图显示失败: {e}")
    
    def update_histogram_display(self) -> None:
        """更新直方图显示"""
        try:
            # 清除现有图形
            self.ax_h.clear()
            self.ax_s.clear()
            self.ax_v.clear()
            
            if self.current_histogram is None:
                # 显示空直方图
                self.ax_h.set_title('H (Hue) - No Data')
                self.ax_s.set_title('S (Saturation) - No Data')
                self.ax_v.set_title('V (Value) - No Data')
            else:
                # H通道直方图
                h_data = self.current_histogram.get('h', [])
                if len(h_data) > 0:
                    self.ax_h.plot(h_data, color='red', linewidth=1.5)
                    self.ax_h.fill_between(range(len(h_data)), h_data, alpha=0.3, color='red')
                self.ax_h.set_title('H (Hue)')
                self.ax_h.set_xlabel('Hue Value (0-179)')
                self.ax_h.set_ylabel('Frequency')
                self.ax_h.grid(True, alpha=0.3)
                
                # S通道直方图
                s_data = self.current_histogram.get('s', [])
                if len(s_data) > 0:
                    self.ax_s.plot(s_data, color='green', linewidth=1.5)
                    self.ax_s.fill_between(range(len(s_data)), s_data, alpha=0.3, color='green')
                self.ax_s.set_title('S (Saturation)')
                self.ax_s.set_xlabel('Saturation Value (0-255)')
                self.ax_s.set_ylabel('Frequency')
                self.ax_s.grid(True, alpha=0.3)
                
                # V通道直方图
                v_data = self.current_histogram.get('v', [])
                if len(v_data) > 0:
                    self.ax_v.plot(v_data, color='blue', linewidth=1.5)
                    self.ax_v.fill_between(range(len(v_data)), v_data, alpha=0.3, color='blue')
                self.ax_v.set_title('V (Value)')
                self.ax_v.set_xlabel('Value (0-255)')
                self.ax_v.set_ylabel('Frequency')
                self.ax_v.grid(True, alpha=0.3)
            
            # 调整布局
            self.fig.tight_layout()
            
            # 刷新画布
            self.histogram_canvas.draw()
            
        except Exception as e:
            logger.error(f"更新直方图显示失败: {e}")
    
    def update_statistics(self, statistics: Dict[str, Any]) -> None:
        """
        更新统计信息显示
        
        Args:
            statistics: 统计信息
        """
        try:
            self.current_statistics = statistics
            
            # 更新显示
            pixel_count = statistics.get('pixel_count', 0)
            coverage_ratio = statistics.get('coverage_ratio', 0.0)
            contour_count = statistics.get('contour_count', 0)
            
            self.pixel_count_var.set(f"{pixel_count:,}")
            self.coverage_var.set(f"{coverage_ratio:.2%}")
            self.contour_count_var.set(str(contour_count))
            
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def on_mask_canvas_configure(self, event) -> None:
        """掩码画布配置变化事件"""
        if self.current_mask is not None:
            self.display_mask_on_canvas()
        else:
            self.show_mask_placeholder()
    
    def export_mask(self) -> None:
        """导出掩码图像"""
        if self.current_mask is None:
            tk.messagebox.showwarning("警告", "没有掩码可导出")
            return
        
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="导出掩码",
                defaultextension=".png",
                filetypes=[("PNG文件", "*.png"), ("JPEG文件", "*.jpg"), ("所有文件", "*.*")]
            )
            
            if filename:
                cv2.imwrite(filename, self.current_mask)
                tk.messagebox.showinfo("成功", f"掩码已导出到: {filename}")
                logger.info(f"掩码已导出: {filename}")
                
        except Exception as e:
            logger.error(f"导出掩码失败: {e}")
            tk.messagebox.showerror("错误", f"导出掩码失败: {e}")
    
    def save_histogram(self) -> None:
        """保存直方图图像"""
        if self.current_histogram is None:
            tk.messagebox.showwarning("警告", "没有直方图可保存")
            return
        
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="保存直方图",
                defaultextension=".png",
                filetypes=[("PNG文件", "*.png"), ("JPEG文件", "*.jpg"), ("PDF文件", "*.pdf")]
            )
            
            if filename:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                tk.messagebox.showinfo("成功", f"直方图已保存到: {filename}")
                logger.info(f"直方图已保存: {filename}")
                
        except Exception as e:
            logger.error(f"保存直方图失败: {e}")
            tk.messagebox.showerror("错误", f"保存直方图失败: {e}")
    
    def toggle_view(self) -> None:
        """切换视图"""
        # 切换到下一个标签页
        current_tab = self.notebook.index(self.notebook.select())
        next_tab = (current_tab + 1) % self.notebook.index("end")
        self.notebook.select(next_tab)
    
    def clear_displays(self) -> None:
        """清空所有显示"""
        self.current_mask = None
        self.current_histogram = None
        self.current_statistics = None
        
        self.show_mask_placeholder()
        self.update_histogram_display()
        self.update_statistics({'pixel_count': 0, 'coverage_ratio': 0.0, 'contour_count': 0}) 