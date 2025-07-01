#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像预览面板模块
实现图像显示和摄像头预览功能
"""

import tkinter as tk
from tkinter import ttk, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class ImagePreviewPanel:
    """图像预览面板类"""
    
    def __init__(self, parent: tk.Widget, on_image_loaded: Optional[Callable] = None):
        """
        初始化图像预览面板
        
        Args:
            parent: 父容器
            on_image_loaded: 图像加载回调函数
        """
        self.parent = parent
        self.on_image_loaded = on_image_loaded
        
        # 当前图像
        self.current_image = None
        self.display_image = None
        
        # 显示参数
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # 创建界面
        self.setup_ui()
        
        logger.debug("图像预览面板初始化完成")
    
    def setup_ui(self) -> None:
        """设置用户界面"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具栏
        self.create_toolbar()
        
        # 图像显示区域
        self.create_image_display()
        
        # 状态信息
        self.create_status_info()
    
    def create_toolbar(self) -> None:
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 加载图片按钮
        load_btn = ttk.Button(toolbar_frame, text="加载图片", 
                             command=self.load_image_file)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 摄像头按钮
        self.camera_btn = ttk.Button(toolbar_frame, text="启动摄像头", 
                                    command=self.toggle_camera)
        self.camera_btn.pack(side=tk.LEFT, padx=5)
        
        # 分隔符
        separator = ttk.Separator(toolbar_frame, orient=tk.VERTICAL)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 缩放控制
        zoom_frame = ttk.Frame(toolbar_frame)
        zoom_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(zoom_frame, text="缩放:").pack(side=tk.LEFT)
        
        zoom_out_btn = ttk.Button(zoom_frame, text="-", width=3,
                                 command=self.zoom_out)
        zoom_out_btn.pack(side=tk.LEFT, padx=(5, 2))
        
        self.zoom_var = tk.StringVar(value="100%")
        zoom_label = ttk.Label(zoom_frame, textvariable=self.zoom_var, width=6)
        zoom_label.pack(side=tk.LEFT, padx=2)
        
        zoom_in_btn = ttk.Button(zoom_frame, text="+", width=3,
                                command=self.zoom_in)
        zoom_in_btn.pack(side=tk.LEFT, padx=(2, 5))
        
        reset_btn = ttk.Button(zoom_frame, text="重置", width=6,
                              command=self.reset_view)
        reset_btn.pack(side=tk.LEFT, padx=5)
    
    def create_image_display(self) -> None:
        """创建图像显示区域"""
        # 创建带滚动条的画布
        canvas_frame = ttk.Frame(self.main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 画布
        self.canvas = tk.Canvas(canvas_frame, bg='gray20', highlightthickness=0)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self.on_canvas_wheel)
        self.canvas.bind("<Button-4>", self.on_canvas_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_canvas_wheel)  # Linux
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 拖拽上传支持（简化版本）
        # 注意：完整的拖拽功能需要额外的依赖包
        
        # 显示提示文本
        self.show_placeholder_text()
    
    def create_status_info(self) -> None:
        """创建状态信息显示"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 图像信息
        self.info_var = tk.StringVar(value="请加载图片或启动摄像头")
        info_label = ttk.Label(status_frame, textvariable=self.info_var, font=("Arial", 9))
        info_label.pack(side=tk.LEFT)
    
    def show_placeholder_text(self) -> None:
        """显示占位符文本"""
        self.canvas.delete("all")
        
        # 获取画布中心
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            center_x = canvas_width // 2
            center_y = canvas_height // 2
            
            # 绘制提示文本
            self.canvas.create_text(center_x, center_y - 20, 
                                  text="拖拽图片到此处", 
                                  fill="gray50", font=("Arial", 14))
            self.canvas.create_text(center_x, center_y + 20, 
                                  text="或点击\"加载图片\"按钮", 
                                  fill="gray50", font=("Arial", 12))
    
    def load_image_file(self) -> None:
        """加载图片文件"""
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
            self.load_image_from_file(filename)
    
    def load_image_from_file(self, filename: str) -> None:
        """
        从文件加载图像
        
        Args:
            filename: 图片文件路径
        """
        try:
            # 读取图像
            image = cv2.imread(filename)
            if image is None:
                raise ValueError("无法读取图片文件")
            
            # 更新显示
            self.update_image(image)
            
            # 更新状态
            height, width = image.shape[:2]
            self.info_var.set(f"图片: {width}x{height} - {filename}")
            
            # 调用回调函数
            if self.on_image_loaded:
                self.on_image_loaded(image)
            
            logger.info(f"图片已加载: {filename}")
            
        except Exception as e:
            logger.error(f"加载图片失败: {e}")
            tk.messagebox.showerror("错误", f"加载图片失败: {e}")
    
    def update_image(self, image: np.ndarray) -> None:
        """
        更新显示图像
        
        Args:
            image: OpenCV图像 (BGR格式)
        """
        try:
            self.current_image = image.copy()
            self.display_image_on_canvas()
            
        except Exception as e:
            logger.error(f"更新图像显示失败: {e}")
    
    def display_image_on_canvas(self) -> None:
        """在画布上显示图像"""
        if self.current_image is None:
            return
        
        try:
            # 转换颜色格式 BGR -> RGB
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            
            # 应用缩放
            height, width = rgb_image.shape[:2]
            new_width = int(width * self.zoom_level)
            new_height = int(height * self.zoom_level)
            
            if self.zoom_level != 1.0:
                rgb_image = cv2.resize(rgb_image, (new_width, new_height), 
                                     interpolation=cv2.INTER_AREA if self.zoom_level < 1.0 else cv2.INTER_CUBIC)
            
            # 转换为PIL图像
            pil_image = Image.fromarray(rgb_image)
            
            # 转换为Tkinter图像
            tk_image = ImageTk.PhotoImage(pil_image)
            
            # 清空画布
            self.canvas.delete("all")
            
            # 显示图像
            self.image_id = self.canvas.create_image(
                self.pan_x, self.pan_y, 
                anchor=tk.NW, 
                image=tk_image
            )
            
            # 保存图像引用（防止被垃圾回收）
            self.canvas.image = tk_image
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # 更新缩放显示
            self.zoom_var.set(f"{int(self.zoom_level * 100)}%")
            
        except Exception as e:
            logger.error(f"显示图像失败: {e}")
    
    def zoom_in(self) -> None:
        """放大图像"""
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.display_image_on_canvas()
    
    def zoom_out(self) -> None:
        """缩小图像"""
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.display_image_on_canvas()
    
    def reset_view(self) -> None:
        """重置视图"""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.display_image_on_canvas()
    
    def on_canvas_click(self, event) -> None:
        """画布点击事件"""
        self.last_x = event.x
        self.last_y = event.y
    
    def on_canvas_drag(self, event) -> None:
        """画布拖拽事件"""
        if hasattr(self, 'last_x') and hasattr(self, 'last_y'):
            dx = event.x - self.last_x
            dy = event.y - self.last_y
            
            self.pan_x += dx
            self.pan_y += dy
            
            # 移动图像
            if hasattr(self, 'image_id'):
                self.canvas.move(self.image_id, dx, dy)
            
            self.last_x = event.x
            self.last_y = event.y
    
    def on_canvas_wheel(self, event) -> None:
        """画布滚轮事件"""
        # 获取缩放方向
        if event.delta > 0 or event.num == 4:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_canvas_configure(self, event) -> None:
        """画布配置变化事件"""
        if self.current_image is None:
            self.show_placeholder_text()
    
    # 文件拖拽功能暂时移除，可以在后续版本中添加
    # 目前通过"加载图片"按钮实现文件选择
    
    def toggle_camera(self) -> None:
        """切换摄像头状态"""
        # 这个功能由主窗口处理
        current_text = self.camera_btn.cget("text")
        if current_text == "启动摄像头":
            self.camera_btn.configure(text="停止摄像头")
        else:
            self.camera_btn.configure(text="启动摄像头")
    
    def set_camera_active(self, active: bool) -> None:
        """
        设置摄像头状态显示
        
        Args:
            active: 是否激活
        """
        if active:
            self.camera_btn.configure(text="停止摄像头")
        else:
            self.camera_btn.configure(text="启动摄像头")
    
    def update_info(self, info_text: str) -> None:
        """
        更新信息显示
        
        Args:
            info_text: 信息文本
        """
        self.info_var.set(info_text)
    
    def get_current_image(self) -> Optional[np.ndarray]:
        """获取当前图像"""
        return self.current_image 