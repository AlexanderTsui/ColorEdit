#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
实现ColorEdit应用程序的主界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import logging
from typing import Optional, Dict, Tuple, Any

from src.core.image_processor import ImageProcessor
from src.core.camera_manager import CameraManager
from src.core.config_manager import ConfigManager
from src.gui.hsv_control_panel import HSVControlPanel
from src.gui.image_preview_panel import ImagePreviewPanel
from src.gui.mask_preview_panel import MaskPreviewPanel
from src.gui.status_bar import StatusBar

logger = logging.getLogger(__name__)

class ColorEditMainWindow:
    """ColorEdit主窗口类"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化主窗口
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.setup_window()
        
        # 核心组件
        self.image_processor = ImageProcessor()
        self.config_manager = ConfigManager()
        self.camera_manager = CameraManager(self.on_camera_frame)
        
        # 当前状态
        self.current_image = None
        self.current_threshold = self.config_manager.get_default_threshold()
        self.current_mask = None
        self.processing_lock = threading.Lock()
        
        # GUI组件
        self.setup_menu()
        self.setup_ui()
        self.setup_bindings()
        
        # 加载预设
        self.config_manager.load_presets()
        
        logger.info("主窗口初始化完成")
    
    def setup_window(self) -> None:
        """设置窗口属性"""
        self.root.title("ColorEdit - 可视化颜色阈值编辑器")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap("assets/icon.ico")
            pass
        except:
            pass
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
    
    def setup_menu(self) -> None:
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图片", command=self.open_image_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="保存配置", command=self.save_config, accelerator="Ctrl+S")
        file_menu.add_command(label="加载配置", command=self.load_config, accelerator="Ctrl+L")
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_window_close, accelerator="Ctrl+Q")
        
        # 摄像头菜单
        camera_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="摄像头", menu=camera_menu)
        camera_menu.add_command(label="启动摄像头", command=self.start_camera)
        camera_menu.add_command(label="停止摄像头", command=self.stop_camera)
        camera_menu.add_separator()
        camera_menu.add_command(label="摄像头设置", command=self.show_camera_settings)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="重置阈值", command=self.reset_threshold)
        tools_menu.add_command(label="颜色预设", command=self.show_color_presets)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def setup_ui(self) -> None:
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建三列布局
        # 左侧：图像预览
        left_frame = ttk.LabelFrame(main_frame, text="图像预览", padding=5)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # 中间：HSV控制面板
        middle_frame = ttk.LabelFrame(main_frame, text="HSV阈值控制", padding=5)
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # 右侧：掩码预览
        right_frame = ttk.LabelFrame(main_frame, text="掩码预览", padding=5)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # 配置列权重
        main_frame.columnconfigure(0, weight=4)  # 左侧图像预览区域最大
        main_frame.columnconfigure(1, weight=1)  # 控制面板较小权重
        main_frame.columnconfigure(2, weight=3)  # 右侧掩码预览区域较大
        main_frame.rowconfigure(0, weight=1)
        
        # 创建子组件
        self.image_preview = ImagePreviewPanel(left_frame, self.on_image_loaded)
        self.hsv_control = HSVControlPanel(middle_frame, self.current_threshold, self.on_threshold_changed)
        self.mask_preview = MaskPreviewPanel(right_frame)
        
        # 状态栏
        self.status_bar = StatusBar(self.root)
        
        # 初始化显示
        self.update_displays()
    
    def setup_bindings(self) -> None:
        """设置键盘快捷键"""
        self.root.bind('<Control-o>', lambda e: self.open_image_file())
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-l>', lambda e: self.load_config())
        self.root.bind('<Control-q>', lambda e: self.on_window_close())
        self.root.bind('<F5>', lambda e: self.process_current_image())
        self.root.bind('<space>', lambda e: self.toggle_camera())
    
    def on_camera_frame(self, frame: np.ndarray) -> None:
        """
        摄像头帧回调函数
        
        Args:
            frame: 摄像头帧图像
        """
        try:
            # 更新图像预览
            self.current_image = frame.copy()
            self.image_preview.update_image(frame)
            
            # 处理图像
            self.process_current_image()
            
            # 更新状态栏
            camera_info = self.camera_manager.get_camera_info()
            if camera_info:
                self.status_bar.update_status(f"摄像头运行中 - FPS: {camera_info.get('current_fps', 0)}")
            
        except Exception as e:
            logger.error(f"处理摄像头帧失败: {e}")
    
    def on_image_loaded(self, image: np.ndarray) -> None:
        """
        图像加载回调函数
        
        Args:
            image: 加载的图像
        """
        self.current_image = image
        self.process_current_image()
        self.status_bar.update_status("图片已加载")
    
    def on_threshold_changed(self, threshold: Dict[str, Tuple[int, int]]) -> None:
        """
        阈值变化回调函数
        
        Args:
            threshold: 新的阈值
        """
        self.current_threshold = threshold
        self.process_current_image()
    
    def process_current_image(self) -> None:
        """处理当前图像"""
        if self.current_image is None:
            return
        
        # 使用锁避免并发处理
        if not self.processing_lock.acquire(blocking=False):
            return
        
        try:
            # 创建掩码
            mask = self.image_processor.create_mask(self.current_image, self.current_threshold)
            self.current_mask = mask
            
            # 更新掩码预览
            self.mask_preview.update_mask(mask)
            
            # 计算和显示直方图
            hsv_image = self.image_processor.convert_to_hsv(self.current_image)
            histogram = self.image_processor.calculate_histogram(hsv_image)
            self.mask_preview.update_histogram(histogram)
            
            # 更新统计信息
            stats = self.image_processor.get_mask_statistics(mask, self.current_image.shape[:2])
            self.mask_preview.update_statistics(stats)
            
        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            messagebox.showerror("错误", f"图像处理失败: {e}")
        finally:
            self.processing_lock.release()
    
    def open_image_file(self) -> None:
        """打开图片文件"""
        file_types = [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=file_types
        )
        
        if filename:
            try:
                # 停止摄像头（如果正在运行）
                if self.camera_manager.is_camera_active():
                    self.camera_manager.stop_camera()
                
                # 加载图片
                image = cv2.imread(filename)
                if image is None:
                    raise ValueError("无法读取图片文件")
                
                # 调整图像大小
                image = self.image_processor.resize_image(image)
                
                # 更新显示
                self.image_preview.update_image(image)
                self.current_image = image
                self.process_current_image()
                
                self.status_bar.update_status(f"已加载图片: {filename}")
                logger.info(f"图片已加载: {filename}")
                
            except Exception as e:
                logger.error(f"加载图片失败: {e}")
                messagebox.showerror("错误", f"加载图片失败: {e}")
    
    def start_camera(self) -> None:
        """启动摄像头"""
        try:
            if self.camera_manager.start_camera():
                self.status_bar.update_status("摄像头已启动")
                logger.info("摄像头已启动")
            else:
                error_msg = self.camera_manager.get_error_message()
                messagebox.showerror("错误", f"启动摄像头失败: {error_msg}")
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            messagebox.showerror("错误", f"启动摄像头失败: {e}")
    
    def stop_camera(self) -> None:
        """停止摄像头"""
        try:
            self.camera_manager.stop_camera()
            self.status_bar.update_status("摄像头已停止")
            logger.info("摄像头已停止")
        except Exception as e:
            logger.error(f"停止摄像头失败: {e}")
    
    def toggle_camera(self) -> None:
        """切换摄像头状态"""
        if self.camera_manager.is_camera_active():
            self.stop_camera()
        else:
            self.start_camera()
    
    def save_config(self) -> None:
        """保存配置"""
        try:
            filepath = self.config_manager.save_threshold_config(
                self.current_threshold,
                description="用户保存的阈值配置"
            )
            self.status_bar.update_status(f"配置已保存: {filepath}")
            messagebox.showinfo("成功", f"配置已保存到: {filepath}")
            logger.info(f"配置已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def load_config(self) -> None:
        """加载配置"""
        file_types = [
            ("JSON配置文件", "*.json"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=file_types
        )
        
        if filename:
            try:
                config_data = self.config_manager.load_threshold_config(filename)
                threshold = config_data['threshold']
                
                # 更新阈值
                self.current_threshold = threshold
                self.hsv_control.update_threshold(threshold)
                
                # 重新处理图像
                self.process_current_image()
                
                self.status_bar.update_status(f"配置已加载: {filename}")
                messagebox.showinfo("成功", f"配置已加载: {config_data.get('name', '未命名')}")
                logger.info(f"配置已加载: {filename}")
                
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                messagebox.showerror("错误", f"加载配置失败: {e}")
    
    def export_config(self) -> None:
        """导出配置"""
        filename = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                self.config_manager.export_config(
                    self.current_threshold,
                    filename,
                    description="导出的阈值配置"
                )
                self.status_bar.update_status(f"配置已导出: {filename}")
                messagebox.showinfo("成功", f"配置已导出到: {filename}")
                logger.info(f"配置已导出: {filename}")
            except Exception as e:
                logger.error(f"导出配置失败: {e}")
                messagebox.showerror("错误", f"导出配置失败: {e}")
    
    def reset_threshold(self) -> None:
        """重置阈值"""
        try:
            default_threshold = self.config_manager.reset_to_defaults()
            self.current_threshold = default_threshold
            self.hsv_control.update_threshold(default_threshold)
            self.process_current_image()
            self.status_bar.update_status("阈值已重置为默认值")
            logger.info("阈值已重置为默认值")
        except Exception as e:
            logger.error(f"重置阈值失败: {e}")
    
    def show_camera_settings(self) -> None:
        """显示摄像头设置"""
        # TODO: 实现摄像头设置对话框
        messagebox.showinfo("提示", "摄像头设置功能正在开发中")
    
    def show_color_presets(self) -> None:
        """显示颜色预设"""
        # TODO: 实现颜色预设对话框
        messagebox.showinfo("提示", "颜色预设功能正在开发中")
    
    def show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
ColorEdit 使用说明:

1. 图像输入:
   - 点击"文件 -> 打开图片"加载本地图片
   - 点击"摄像头 -> 启动摄像头"使用实时摄像头

2. 阈值调节:
   - 使用中间面板的滑块调节HSV阈值
   - H（色相）: 0-179
   - S（饱和度）: 0-255  
   - V（明度）: 0-255

3. 配置管理:
   - Ctrl+S: 保存当前阈值配置
   - Ctrl+L: 加载配置文件
   - 支持导出配置到指定位置

4. 快捷键:
   - Space: 启动/停止摄像头
   - F5: 刷新处理
   - Ctrl+Q: 退出应用程序
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self) -> None:
        """显示关于信息"""
        about_text = """
ColorEdit v1.0.0

可视化颜色阈值编辑器

类似OpenMV的HSV颜色检测工具，支持实时摄像头预览和图片处理。

开发: Python + OpenCV + Tkinter
        """
        messagebox.showinfo("关于", about_text)
    
    def update_displays(self) -> None:
        """更新所有显示"""
        # 如果有图像，处理并显示
        if self.current_image is not None:
            self.process_current_image()
    
    def on_window_close(self) -> None:
        """窗口关闭事件处理"""
        try:
            # 停止摄像头
            if self.camera_manager.is_camera_active():
                self.camera_manager.stop_camera()
            
            # 保存窗口状态等
            logger.info("应用程序正在关闭")
            
            # 销毁窗口
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"关闭应用程序时出错: {e}")
            self.root.destroy() 