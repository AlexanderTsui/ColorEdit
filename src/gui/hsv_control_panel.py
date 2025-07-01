#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HSV控制面板模块
实现HSV三通道滑块控制界面
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Tuple, Callable, Optional

logger = logging.getLogger(__name__)

class HSVControlPanel:
    """HSV控制面板类"""
    
    def __init__(self, parent: tk.Widget, initial_threshold: Dict[str, Tuple[int, int]], 
                 on_threshold_changed: Callable[[Dict[str, Tuple[int, int]]], None]):
        """
        初始化HSV控制面板
        
        Args:
            parent: 父容器
            initial_threshold: 初始阈值
            on_threshold_changed: 阈值变化回调函数
        """
        self.parent = parent
        self.threshold = initial_threshold.copy()
        self.on_threshold_changed = on_threshold_changed
        
        # 创建界面
        self.setup_ui()
        
        # 更新显示
        self.update_threshold(initial_threshold)
        
        logger.debug("HSV控制面板初始化完成")
    
    def setup_ui(self) -> None:
        """设置用户界面"""
        # 主框架
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # H通道控制
        self.create_channel_control("H (色相)", "h", 0, 179, "#FF6B6B", 0)
        
        # S通道控制
        self.create_channel_control("S (饱和度)", "s", 0, 255, "#4ECDC4", 1)
        
        # V通道控制
        self.create_channel_control("V (明度)", "v", 0, 255, "#45B7D1", 2)
        
        # 预设按钮框架
        self.create_preset_buttons()
        
        # 操作按钮框架
        self.create_action_buttons()
    
    def create_channel_control(self, label: str, channel: str, min_val: int, max_val: int, 
                             color: str, row: int) -> None:
        """
        创建单个通道的控制组件
        
        Args:
            label: 通道标签
            channel: 通道名称 ('h', 's', 'v')
            min_val: 最小值
            max_val: 最大值
            color: 通道颜色
            row: 行位置
        """
        # 通道框架
        channel_frame = ttk.LabelFrame(self.main_frame, text=label, padding=10)
        channel_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        
        # 数值输入框架
        values_frame = ttk.Frame(channel_frame)
        values_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 最小值输入
        min_label = ttk.Label(values_frame, text="最小值:")
        min_label.grid(row=0, column=0, padx=(0, 5), sticky="w")
        
        min_var = tk.IntVar(value=self.threshold[channel][0])
        min_spinbox = ttk.Spinbox(values_frame, from_=min_val, to=max_val, 
                                 width=8, textvariable=min_var,
                                 command=lambda: self.on_value_changed(channel, 0, min_var.get()))
        min_spinbox.grid(row=0, column=1, padx=(0, 20), sticky="w")
        min_spinbox.bind('<Return>', lambda e: self.on_value_changed(channel, 0, min_var.get()))
        min_spinbox.bind('<FocusOut>', lambda e: self.on_value_changed(channel, 0, min_var.get()))
        
        # 最大值输入
        max_label = ttk.Label(values_frame, text="最大值:")
        max_label.grid(row=0, column=2, padx=(0, 5), sticky="w")
        
        max_var = tk.IntVar(value=self.threshold[channel][1])
        max_spinbox = ttk.Spinbox(values_frame, from_=min_val, to=max_val, 
                                 width=8, textvariable=max_var,
                                 command=lambda: self.on_value_changed(channel, 1, max_var.get()))
        max_spinbox.grid(row=0, column=3, sticky="w")
        max_spinbox.bind('<Return>', lambda e: self.on_value_changed(channel, 1, max_var.get()))
        max_spinbox.bind('<FocusOut>', lambda e: self.on_value_changed(channel, 1, max_var.get()))
        
        # 滑块框架
        slider_frame = ttk.Frame(channel_frame)
        slider_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 范围滑块（使用两个独立的滑块模拟范围滑块）
        min_slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                              variable=min_var,
                              command=lambda v: self.on_slider_changed(channel, 0, int(float(v))))
        min_slider.pack(fill=tk.X, pady=(0, 2))
        
        max_slider = ttk.Scale(slider_frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                              variable=max_var,
                              command=lambda v: self.on_slider_changed(channel, 1, int(float(v))))
        max_slider.pack(fill=tk.X)
        
        # 颜色预览条
        if channel == 'h':
            self.create_hue_preview(channel_frame)
        else:
            self.create_color_preview(channel_frame, color)
        
        # 保存组件引用
        setattr(self, f"{channel}_min_var", min_var)
        setattr(self, f"{channel}_max_var", max_var)
        setattr(self, f"{channel}_min_slider", min_slider)
        setattr(self, f"{channel}_max_slider", max_slider)
    
    def create_hue_preview(self, parent: tk.Widget) -> None:
        """
        创建色相预览条
        
        Args:
            parent: 父容器
        """
        preview_frame = ttk.Frame(parent)
        preview_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 色相预览画布
        canvas = tk.Canvas(preview_frame, height=20, bg='white')
        canvas.pack(fill=tk.X)
        
        # 绘制色相渐变
        width = 300  # 默认宽度
        for i in range(width):
            hue = int(i * 179 / width)
            color = self.hsv_to_hex(hue, 255, 255)
            canvas.create_line(i, 0, i, 20, fill=color, width=1)
        
        setattr(self, "h_preview_canvas", canvas)
        
        # 绑定画布大小变化事件
        canvas.bind('<Configure>', self.on_hue_canvas_configure)
    
    def create_color_preview(self, parent: tk.Widget, color: str) -> None:
        """
        创建颜色预览条
        
        Args:
            parent: 父容器
            color: 预览颜色
        """
        preview_frame = ttk.Frame(parent)
        preview_frame.pack(fill=tk.X, pady=(5, 0))
        
        canvas = tk.Canvas(preview_frame, height=20, bg=color)
        canvas.pack(fill=tk.X)
    
    def create_preset_buttons(self) -> None:
        """创建预设按钮"""
        preset_frame = ttk.LabelFrame(self.main_frame, text="颜色预设", padding=10)
        preset_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
        
        # 预设颜色
        presets = [
            ("红色", {'h': (0, 10), 's': (100, 255), 'v': (50, 255)}),
            ("绿色", {'h': (40, 70), 's': (100, 255), 'v': (50, 255)}),
            ("蓝色", {'h': (100, 130), 's': (100, 255), 'v': (50, 255)}),
            ("黄色", {'h': (20, 30), 's': (100, 255), 'v': (100, 255)})
        ]
        
        for i, (name, threshold) in enumerate(presets):
            btn = ttk.Button(preset_frame, text=name, width=8,
                           command=lambda t=threshold: self.apply_preset(t))
            btn.grid(row=i//2, column=i%2, padx=2, pady=2, sticky="ew")
        
        # 配置列权重
        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)
    
    def create_action_buttons(self) -> None:
        """创建操作按钮"""
        action_frame = ttk.LabelFrame(self.main_frame, text="操作", padding=10)
        action_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        
        # 重置按钮
        reset_btn = ttk.Button(action_frame, text="重置", 
                             command=self.reset_threshold)
        reset_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 反转按钮
        invert_btn = ttk.Button(action_frame, text="反转", 
                              command=self.invert_threshold)
        invert_btn.pack(side=tk.LEFT, padx=5)
        
        # 微调按钮
        fine_tune_btn = ttk.Button(action_frame, text="精细调节", 
                                 command=self.show_fine_tune)
        fine_tune_btn.pack(side=tk.LEFT, padx=5)
    
    def on_value_changed(self, channel: str, index: int, value: int) -> None:
        """
        处理数值变化
        
        Args:
            channel: 通道名称
            index: 索引 (0=最小值, 1=最大值)
            value: 新值
        """
        try:
            # 验证值的有效性
            if channel == 'h':
                value = max(0, min(179, value))
            else:
                value = max(0, min(255, value))
            
            # 更新阈值
            current_values = list(self.threshold[channel])
            current_values[index] = value
            
            # 确保最小值不大于最大值
            if index == 0 and current_values[0] > current_values[1]:
                current_values[1] = current_values[0]
            elif index == 1 and current_values[1] < current_values[0]:
                current_values[0] = current_values[1]
            
            self.threshold[channel] = tuple(current_values)
            
            # 更新滑块
            getattr(self, f"{channel}_min_var").set(self.threshold[channel][0])
            getattr(self, f"{channel}_max_var").set(self.threshold[channel][1])
            
            # 触发回调
            self.on_threshold_changed(self.threshold.copy())
            
        except Exception as e:
            logger.error(f"处理数值变化失败: {e}")
    
    def on_slider_changed(self, channel: str, index: int, value: int) -> None:
        """
        处理滑块变化
        
        Args:
            channel: 通道名称
            index: 索引 (0=最小值, 1=最大值)
            value: 新值
        """
        self.on_value_changed(channel, index, value)
    
    def on_hue_canvas_configure(self, event) -> None:
        """色相画布大小变化事件"""
        try:
            canvas = event.widget
            canvas.delete("all")
            
            width = canvas.winfo_width()
            if width > 1:
                # 重新绘制色相渐变
                for i in range(width):
                    hue = int(i * 179 / width)
                    color = self.hsv_to_hex(hue, 255, 255)
                    canvas.create_line(i, 0, i, 20, fill=color, width=1)
        except Exception as e:
            logger.error(f"更新色相预览失败: {e}")
    
    def hsv_to_hex(self, h: int, s: int, v: int) -> str:
        """
        将HSV转换为十六进制颜色
        
        Args:
            h: 色相 (0-179)
            s: 饱和度 (0-255)
            v: 明度 (0-255)
            
        Returns:
            十六进制颜色字符串
        """
        import colorsys
        
        # 转换为0-1范围
        h_norm = h / 179.0
        s_norm = s / 255.0
        v_norm = v / 255.0
        
        # 转换为RGB
        r, g, b = colorsys.hsv_to_rgb(h_norm, s_norm, v_norm)
        
        # 转换为0-255范围并格式化为十六进制
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)
        
        return f"#{r_int:02x}{g_int:02x}{b_int:02x}"
    
    def apply_preset(self, preset_threshold: Dict[str, Tuple[int, int]]) -> None:
        """
        应用预设阈值
        
        Args:
            preset_threshold: 预设阈值
        """
        try:
            self.update_threshold(preset_threshold)
            self.on_threshold_changed(self.threshold.copy())
            logger.info("预设阈值已应用")
        except Exception as e:
            logger.error(f"应用预设失败: {e}")
    
    def reset_threshold(self) -> None:
        """重置阈值为默认值"""
        default_threshold = {
            'h': (0, 179),
            's': (0, 255),
            'v': (0, 255)
        }
        self.update_threshold(default_threshold)
        self.on_threshold_changed(self.threshold.copy())
        logger.info("阈值已重置")
    
    def invert_threshold(self) -> None:
        """反转阈值"""
        try:
            inverted = {}
            for channel, (min_val, max_val) in self.threshold.items():
                if channel == 'h':
                    # 色相反转比较复杂，这里简化处理
                    mid = (min_val + max_val) // 2
                    new_min = (mid + 90) % 180
                    new_max = (mid - 90) % 180
                    if new_min > new_max:
                        new_min, new_max = new_max, new_min
                    inverted[channel] = (new_min, new_max)
                else:
                    # S和V通道反转
                    inverted[channel] = (255 - max_val, 255 - min_val)
            
            self.update_threshold(inverted)
            self.on_threshold_changed(self.threshold.copy())
            logger.info("阈值已反转")
        except Exception as e:
            logger.error(f"反转阈值失败: {e}")
    
    def show_fine_tune(self) -> None:
        """显示精细调节窗口"""
        # TODO: 实现精细调节窗口
        import tkinter.messagebox as msgbox
        msgbox.showinfo("提示", "精细调节功能正在开发中")
    
    def update_threshold(self, threshold: Dict[str, Tuple[int, int]]) -> None:
        """
        更新阈值显示
        
        Args:
            threshold: 新阈值
        """
        try:
            self.threshold = threshold.copy()
            
            # 更新各通道的显示
            for channel in ['h', 's', 'v']:
                min_val, max_val = self.threshold[channel]
                
                # 更新变量
                getattr(self, f"{channel}_min_var").set(min_val)
                getattr(self, f"{channel}_max_var").set(max_val)
            
            logger.debug(f"阈值显示已更新: {threshold}")
            
        except Exception as e:
            logger.error(f"更新阈值显示失败: {e}")
    
    def get_threshold(self) -> Dict[str, Tuple[int, int]]:
        """获取当前阈值"""
        return self.threshold.copy() 