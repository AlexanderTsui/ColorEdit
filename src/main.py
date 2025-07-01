#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ColorEdit - 可视化颜色阈值编辑器
主程序入口文件
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.main_window import ColorEditMainWindow
from src.utils.logger import setup_logger

def main():
    """主函数"""
    # 设置日志
    logger = setup_logger()
    logger.info("启动 ColorEdit 应用程序")
    
    try:
        # 创建主窗口
        root = tk.Tk()
        app = ColorEditMainWindow(root)
        
        # 启动应用
        root.mainloop()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        sys.exit(1)
    
    logger.info("ColorEdit 应用程序已退出")

if __name__ == "__main__":
    main() 