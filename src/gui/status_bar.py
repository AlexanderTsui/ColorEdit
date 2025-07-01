#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态栏模块
实现应用程序底部状态栏显示
"""

import tkinter as tk
from tkinter import ttk
import logging
from datetime import datetime
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

class StatusBar:
    """状态栏类"""
    
    def __init__(self, parent: tk.Widget):
        """
        初始化状态栏
        
        Args:
            parent: 父容器
        """
        self.parent = parent
        
        # 状态变量
        self.status_text = ""
        self.progress_value = 0
        self.fps_count = 0
        self.memory_usage = 0
        
        # 时钟更新线程
        self.clock_running = True
        
        # 创建界面
        self.setup_ui()
        
        # 启动时钟更新
        self.start_clock_update()
        
        logger.debug("状态栏初始化完成")
    
    def setup_ui(self) -> None:
        """设置用户界面"""
        # 状态栏主框架
        self.status_frame = ttk.Frame(self.parent, relief=tk.SUNKEN, borderwidth=1)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建各个状态区域
        self.create_status_widgets()
    
    def create_status_widgets(self) -> None:
        """创建状态栏控件"""
        # 主状态文本
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, 
                               font=("Arial", 9))
        status_label.pack(side=tk.LEFT, padx=(5, 20))
        
        # 分隔符1
        separator1 = ttk.Separator(self.status_frame, orient=tk.VERTICAL)
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 进度条区域
        progress_frame = ttk.Frame(self.status_frame)
        progress_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(progress_frame, text="处理:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, length=100, 
                                          variable=self.progress_var, 
                                          maximum=100, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=(5, 5))
        
        self.progress_text_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_text_var, 
                 font=("Arial", 8), width=4).pack(side=tk.LEFT)
        
        # 分隔符2
        separator2 = ttk.Separator(self.status_frame, orient=tk.VERTICAL)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # FPS显示
        fps_frame = ttk.Frame(self.status_frame)
        fps_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(fps_frame, text="FPS:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="0")
        ttk.Label(fps_frame, textvariable=self.fps_var, 
                 font=("Arial", 8, "bold"), width=4).pack(side=tk.LEFT, padx=(5, 0))
        
        # 分隔符3
        separator3 = ttk.Separator(self.status_frame, orient=tk.VERTICAL)
        separator3.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 内存使用显示
        memory_frame = ttk.Frame(self.status_frame)
        memory_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(memory_frame, text="内存:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.memory_var = tk.StringVar(value="0 MB")
        ttk.Label(memory_frame, textvariable=self.memory_var, 
                 font=("Arial", 8), width=8).pack(side=tk.LEFT, padx=(5, 0))
        
        # 分隔符4
        separator4 = ttk.Separator(self.status_frame, orient=tk.VERTICAL)
        separator4.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # 时钟显示
        self.time_var = tk.StringVar(value=datetime.now().strftime("%H:%M:%S"))
        time_label = ttk.Label(self.status_frame, textvariable=self.time_var, 
                              font=("Arial", 9))
        time_label.pack(side=tk.RIGHT, padx=(20, 5))
        
        # 日期显示
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_label = ttk.Label(self.status_frame, textvariable=self.date_var, 
                              font=("Arial", 8))
        date_label.pack(side=tk.RIGHT, padx=(0, 10))
    
    def update_status(self, status: str) -> None:
        """
        更新状态文本
        
        Args:
            status: 状态文本
        """
        try:
            self.status_text = status
            self.status_var.set(status)
            logger.debug(f"状态更新: {status}")
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    def update_progress(self, value: int, text: str = None) -> None:
        """
        更新进度条
        
        Args:
            value: 进度值 (0-100)
            text: 进度文本
        """
        try:
            value = max(0, min(100, value))  # 确保在0-100范围内
            self.progress_value = value
            self.progress_var.set(value)
            
            if text is None:
                text = f"{value}%"
            self.progress_text_var.set(text)
            
        except Exception as e:
            logger.error(f"更新进度失败: {e}")
    
    def update_fps(self, fps: int) -> None:
        """
        更新FPS显示
        
        Args:
            fps: 帧率
        """
        try:
            self.fps_count = fps
            self.fps_var.set(str(fps))
        except Exception as e:
            logger.error(f"更新FPS失败: {e}")
    
    def update_memory(self, memory_mb: float) -> None:
        """
        更新内存使用显示
        
        Args:
            memory_mb: 内存使用量（MB）
        """
        try:
            self.memory_usage = memory_mb
            if memory_mb < 1024:
                memory_text = f"{memory_mb:.1f} MB"
            else:
                memory_text = f"{memory_mb/1024:.1f} GB"
            self.memory_var.set(memory_text)
        except Exception as e:
            logger.error(f"更新内存使用失败: {e}")
    
    def start_clock_update(self) -> None:
        """启动时钟更新线程"""
        def update_clock():
            while self.clock_running:
                try:
                    now = datetime.now()
                    self.time_var.set(now.strftime("%H:%M:%S"))
                    
                    # 每分钟更新一次日期
                    if now.second == 0:
                        self.date_var.set(now.strftime("%Y-%m-%d"))
                    
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"时钟更新失败: {e}")
                    time.sleep(1)
        
        self.clock_thread = threading.Thread(target=update_clock, daemon=True)
        self.clock_thread.start()
    
    def stop_clock_update(self) -> None:
        """停止时钟更新线程"""
        self.clock_running = False
    
    def show_progress(self, show: bool = True) -> None:
        """
        显示或隐藏进度条
        
        Args:
            show: 是否显示
        """
        try:
            if show:
                self.progress_bar.pack(side=tk.LEFT, padx=(5, 5))
            else:
                self.progress_bar.pack_forget()
        except Exception as e:
            logger.error(f"切换进度条显示失败: {e}")
    
    def reset_progress(self) -> None:
        """重置进度条"""
        self.update_progress(0, "0%")
    
    def set_busy(self, busy: bool = True) -> None:
        """
        设置忙碌状态
        
        Args:
            busy: 是否忙碌
        """
        try:
            if busy:
                self.update_status("处理中...")
                self.progress_bar.configure(mode='indeterminate')
                self.progress_bar.start()
                self.progress_text_var.set("...")
            else:
                self.progress_bar.stop()
                self.progress_bar.configure(mode='determinate')
                self.update_status("就绪")
                self.reset_progress()
        except Exception as e:
            logger.error(f"设置忙碌状态失败: {e}")
    
    def get_current_memory_usage(self) -> float:
        """
        获取当前进程内存使用量
        
        Returns:
            内存使用量（MB）
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB
            
            return memory_mb
        except ImportError:
            # 如果没有psutil，返回估算值
            return 50.0
        except Exception as e:
            logger.error(f"获取内存使用失败: {e}")
            return 0.0
    
    def auto_update_memory(self, interval: int = 5) -> None:
        """
        自动更新内存使用显示
        
        Args:
            interval: 更新间隔（秒）
        """
        def update_memory():
            while self.clock_running:
                try:
                    memory_usage = self.get_current_memory_usage()
                    self.update_memory(memory_usage)
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"自动内存更新失败: {e}")
                    time.sleep(interval)
        
        memory_thread = threading.Thread(target=update_memory, daemon=True)
        memory_thread.start()
    
    def update_all(self, status: str = None, progress: int = None, 
                   fps: int = None, memory: float = None) -> None:
        """
        一次性更新多个状态
        
        Args:
            status: 状态文本
            progress: 进度值
            fps: 帧率
            memory: 内存使用量
        """
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
            logger.error(f"批量更新状态失败: {e}")
    
    def clear_all(self) -> None:
        """清空所有状态显示"""
        self.update_status("就绪")
        self.reset_progress()
        self.update_fps(0)
        self.update_memory(0)
    
    def __del__(self):
        """析构函数"""
        self.stop_clock_update() 