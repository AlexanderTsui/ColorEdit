# ColorEdit - 可视化颜色阈值编辑器

## UI Refresh (v1.1.0)

This project now uses a redesigned **pink-tone Qt UI** while keeping the original HSV-mask workflow unchanged.

### New UI highlights
- Pink visual theme with rounded cards, slider accents, and soft gradient background.
- Dynamic sakura (cherry blossom) animation overlay designed for low CPU usage.
- Layout can be changed in two ways:
  - Preset layout switch: **Three Columns** / **Top-Bottom**.
  - Drag-resize layout with splitter handles.
- All original core functions are preserved:
  - HSV min/max threshold dragging (H/S/V)
  - Real-time mask preview for camera and image input
  - Histogram/statistics view
  - Config save/load/export

### Run (Windows PowerShell)
```powershell
.\myenv\Scripts\Activate.ps1
python run_coloredit.py
```

If `Activate.ps1` is blocked by execution policy, use:
```powershell
.\myenv\Scripts\python.exe run_coloredit.py
```


## 项目简介

ColorEdit 是一个基于 Python 的可视化颜色阈值编辑器，类似于 OpenMV IDE 的颜色阈值功能。用户可以通过拖动 HSV 三通道的高低阈值滑块，实时预览摄像头或指定图片中的掩码图像。该工具特别适用于计算机视觉项目中的颜色检测和分割任务的参数调试。

![ColorEdit界面预览](docs/screenshot.png)

## 功能特性

### 核心功能
- 🎨 **HSV 颜色空间编辑**: 支持 H（色相）、S（饱和度）、V（明度）三通道独立调节
- 📹 **实时摄像头预览**: 支持摄像头实时图像处理和掩码显示
- 🖼️ **图片文件处理**: 支持加载 JPG、PNG、BMP 等格式图片进行颜色阈值编辑
- 🎯 **实时掩码预览**: 根据设定的阈值实时显示二值化掩码图像
- 📊 **HSV直方图显示**: 实时显示图像HSV各通道的直方图分布
- 💾 **参数保存/加载**: 支持保存和加载颜色阈值参数配置

### 高级功能
- 🎛️ **颜色预设模板**: 内置常用颜色（红、绿、蓝、黄等）的阈值预设
- 📈 **统计信息显示**: 显示掩码像素数量、覆盖率、轮廓数量等统计信息
- 🚀 **高性能处理**: 多线程图像处理，支持实时预览
- 💻 **桌面应用**: 原生桌面应用，无需浏览器，启动快速
- ⌨️ **快捷键支持**: 支持常用操作的键盘快捷键

## 技术栈

### 核心技术
- **语言**: Python 3.7+
- **GUI框架**: Tkinter (Python 标准库)
- **图像处理**: OpenCV-Python 4.x
- **科学计算**: NumPy
- **图像显示**: Pillow (PIL)
- **绘图**: Matplotlib

### 开发工具
- **依赖管理**: pip + requirements.txt
- **代码规范**: Python PEP 8
- **版本控制**: Git
- **文档**: Markdown

## 项目结构

```
ColorEdit/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── main.py            # 应用程序入口
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   ├── image_processor.py     # 图像处理核心
│   │   ├── camera_manager.py      # 摄像头管理
│   │   └── config_manager.py      # 配置管理
│   ├── gui/               # 图形界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口
│   │   ├── hsv_control_panel.py   # HSV控制面板
│   │   ├── image_preview_panel.py # 图像预览面板
│   │   ├── mask_preview_panel.py  # 掩码预览面板
│   │   └── status_bar.py          # 状态栏
│   └── utils/             # 工具函数
│       ├── __init__.py
│       └── logger.py      # 日志工具
├── config/                # 配置文件目录
│   └── default.json       # 默认配置和颜色预设
├── docs/                  # 项目文档
│   ├── TECHNICAL_DESIGN.md
│   └── UI_DESIGN.md
├── requirements.txt       # Python依赖列表
├── run_coloredit.py      # 启动脚本
└── README.md
```

## 快速开始

### 环境要求
- Python 3.7 或更高版本
- Windows / macOS / Linux
- 摄像头设备（可选，用于实时预览）

### 安装步骤

1. **克隆或下载项目**
```bash
git clone https://github.com/AlexanderTsui/ColorEdit.git
cd ColorEdit
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
python run_coloredit.py
```

### 依赖说明

主要依赖包：
- `opencv-python>=4.5.0` - 图像处理核心库
- `numpy>=1.19.0` - 数值计算
- `Pillow>=8.0.0` - 图像显示
- `matplotlib>=3.3.0` - 直方图绘制

```bash
# 也可以单独安装依赖
pip install opencv-python numpy Pillow matplotlib
```

## 使用指南

### 界面布局

新版界面采用"顶部操作条 + 中部三栏主体 + 底部状态栏"的结构：
- **顶部操作条**: 集中放置打开图片、摄像头启停、配置保存/加载等高频操作
- **中部左栏 (Image Feed)**: 显示原图或摄像头画面，支持缩放与拖拽查看
- **中部中栏 (HSV Controls)**: H/S/V 三通道阈值卡片化控制，包含预设与快捷操作按钮
- **中部右栏 (Mask Analysis)**: 掩码结果与 HSV 直方图标签页，底部显示像素统计与导出操作
- **底部状态栏**: 显示运行状态、处理进度、FPS、内存与时间信息

### 基本操作

#### 1. 加载图片
- 点击"加载图片"按钮选择本地图片文件
- 支持格式：JPG、JPEG、PNG、BMP、TIFF
- 图片将自动调整大小以适应显示区域

#### 2. 启动摄像头
- 点击"启动摄像头"按钮
- 首次使用需要允许摄像头访问权限
- 实时画面将显示在左侧预览区域

#### 3. 调节HSV阈值
- **H (色相)**: 调节颜色类型，范围 0-179
- **S (饱和度)**: 调节颜色纯度，范围 0-255  
- **V (明度)**: 调节颜色亮度，范围 0-255
- 每个通道都有最小值和最大值滑块
- 实时查看右侧掩码效果

#### 4. 查看处理结果
- **掩码标签页**: 显示二值化掩码图像
- **直方图标签页**: 显示HSV各通道的分布直方图
- **统计信息**: 像素数量、覆盖率、轮廓数量

#### 5. 保存和加载配置
- **保存配置**: `Ctrl+S` 或菜单"文件→保存配置"
- **加载配置**: `Ctrl+L` 或菜单"文件→加载配置"
- 配置文件为JSON格式，包含HSV阈值参数

### 高级功能

#### 颜色预设
应用内置了常用颜色的预设阈值：
- 红色、绿色、蓝色
- 黄色、橙色、紫色、青色
- 白色、黑色

点击预设按钮可快速应用对应的HSV阈值。

#### 键盘快捷键
- `Ctrl+O`: 打开图片文件
- `Ctrl+S`: 保存当前配置
- `Ctrl+L`: 加载配置文件
- `Space`: 启动/停止摄像头
- `F5`: 手动刷新处理
- `Ctrl+Q`: 退出应用

## 配置文件格式

```json
{
  "default_threshold": {
    "h": [0, 179],
    "s": [0, 255], 
    "v": [0, 255]
  },
  "presets": {
    "红色": {
      "h": [0, 10],
      "s": [120, 255],
      "v": [70, 255]
    }
  }
}
```

## 开发指南

### 代码结构说明

- **core/**: 核心业务逻辑
  - `image_processor.py`: 图像处理算法
  - `camera_manager.py`: 摄像头控制
  - `config_manager.py`: 配置文件管理

- **gui/**: 用户界面组件
  - `main_window.py`: 主窗口布局
  - `*_panel.py`: 各功能面板

### 扩展开发

#### 添加新的颜色预设
编辑 `config/default.json` 文件：
```json
"presets": {
  "新颜色": {
    "h": [最小色相, 最大色相],
    "s": [最小饱和度, 最大饱和度], 
    "v": [最小明度, 最大明度]
  }
}
```

#### 自定义图像处理算法
继承或修改 `src/core/image_processor.py` 中的 `ImageProcessor` 类。

### 调试和日志

应用使用 Python 标准 logging 模块：
- 日志级别：DEBUG、INFO、WARNING、ERROR
- 控制台输出：运行时信息
- 异常处理：用户友好的错误提示

## 故障排除

### 常见问题

1. **摄像头无法启动**
   - 检查摄像头是否被其他程序占用
   - 确认系统摄像头权限设置
   - 尝试重新插拔USB摄像头

2. **图片无法加载**
   - 检查图片文件格式是否支持
   - 确认文件路径中没有特殊字符
   - 尝试转换图片格式

3. **依赖安装失败**
   - 更新 pip: `pip install --upgrade pip`
   - 使用清华源: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`
   - 检查Python版本是否符合要求

4. **界面显示异常**
   - 检查系统DPI设置
   - 尝试调整窗口大小
   - 重启应用程序

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 更新日志

### v1.0.0 (2024-07-01)
- ✨ 初始版本发布
- ✨ 支持HSV阈值调节
- ✨ 摄像头实时预览
- ✨ 图片加载处理
- ✨ 掩码显示和直方图
- ✨ 配置保存/加载
- ✨ 颜色预设模板

## 贡献指南

欢迎提交问题和改进建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 联系方式

- 项目主页: https://github.com/AlexanderTsui/ColorEdit
- 问题反馈: https://github.com/AlexanderTsui/ColorEdit/issues
- 邮箱: 1483237499@qq.com

## 致谢

感谢以下开源项目的支持：
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [NumPy](https://numpy.org/) - 科学计算
- [Matplotlib](https://matplotlib.org/) - 绘图库
- [Pillow](https://pillow.readthedocs.io/) - 图像处理
- Python 社区的所有贡献者

---

如果觉得这个项目对你有帮助，请考虑给个 ⭐️ Star！ 
