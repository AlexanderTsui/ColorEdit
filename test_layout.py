#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
布局测试脚本
快速测试界面布局变化
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_test_window():
    """创建测试窗口显示布局"""
    root = tk.Tk()
    root.title("ColorEdit 布局测试")
    root.geometry("1200x800")
    
    # 主框架
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 创建三列布局
    # 左侧：图像预览（权重=4，最大）
    left_frame = ttk.LabelFrame(main_frame, text="图像预览区域 (权重=4)", padding=5)
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    
    # 中间：HSV控制面板（权重=1，最小）
    middle_frame = ttk.LabelFrame(main_frame, text="HSV控制面板 (权重=1)", padding=5)
    middle_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    
    # 右侧：掩码预览（权重=3，较大）
    right_frame = ttk.LabelFrame(main_frame, text="掩码预览区域 (权重=3)", padding=5)
    right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
    
    # 配置列权重（新的布局）
    main_frame.columnconfigure(0, weight=4)  # 左侧最大
    main_frame.columnconfigure(1, weight=1)  # 控制面板最小
    main_frame.columnconfigure(2, weight=3)  # 右侧较大
    main_frame.rowconfigure(0, weight=1)
    
    # 在每个区域添加提示文本
    ttk.Label(left_frame, text="这里显示原图片/摄像头画面\n现在占用最多空间 (4:1:3)", 
             font=("Arial", 12), foreground="blue").pack(expand=True)
    
    ttk.Label(middle_frame, text="HSV\n阈值\n控制\n滑块", 
             font=("Arial", 10), foreground="green").pack(expand=True)
    
    ttk.Label(right_frame, text="这里显示掩码结果\n和直方图", 
             font=("Arial", 12), foreground="red").pack(expand=True)
    
    # 状态栏
    status_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=1)
    status_frame.pack(side=tk.BOTTOM, fill=tk.X)
    ttk.Label(status_frame, text="状态: 布局已调整 - 左侧图像预览区域权重=4 (最大)", 
             font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
    
    return root

def main():
    """主函数"""
    print("ColorEdit 布局测试")
    print("左侧图像预览区域权重: 4")
    print("中间HSV控制面板权重: 1") 
    print("右侧掩码预览区域权重: 3") 
    print("比例 = 4:1:3，左侧最大，右侧其次，中间最小")
    print("关闭窗口退出测试...")
    
    root = create_test_window()
    root.mainloop()

if __name__ == "__main__":
    main() 