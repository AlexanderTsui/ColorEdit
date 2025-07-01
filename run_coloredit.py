#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ColorEdit 启动脚本
快速启动 ColorEdit 应用程序
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import matplotlib
    except ImportError:
        missing_deps.append("matplotlib")
    
    if missing_deps:
        print("错误：缺少以下依赖包：")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖：")
        print(f"pip install {' '.join(missing_deps)}")
        print("\n或者运行：")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("ColorEdit - 可视化颜色阈值编辑器")
    print("版本: 1.0.0")
    print("=" * 50)
    
    # 检查依赖
    print("检查依赖包...")
    if not check_dependencies():
        sys.exit(1)
    
    print("依赖检查通过 ✓")
    print("启动应用程序...")
    
    try:
        # 导入并启动应用
        from src.main import main as app_main
        app_main()
        
    except KeyboardInterrupt:
        print("\n应用程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n可能的解决方案：")
        print("1. 检查Python版本（需要3.7+）")
        print("2. 重新安装依赖: pip install -r requirements.txt")
        print("3. 确保摄像头没有被其他程序占用")
        sys.exit(1)

if __name__ == "__main__":
    main() 