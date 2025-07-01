#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理模块
实现HSV颜色空间转换、阈值处理、掩码生成等核心功能
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图像处理器类"""
    
    def __init__(self):
        """初始化图像处理器"""
        self.last_processed_image = None
        self.last_mask = None
        self.last_histogram = None
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        Args:
            image: 输入图像 (BGR格式)
            
        Returns:
            预处理后的图像
        """
        if image is None:
            raise ValueError("输入图像不能为空")
        
        # 高斯模糊去噪
        processed = cv2.GaussianBlur(image, (5, 5), 0)
        
        # 可选：直方图均衡化增强对比度
        # lab = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
        # lab[:, :, 0] = cv2.equalizeHist(lab[:, :, 0])
        # processed = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        return processed
    
    def convert_to_hsv(self, image: np.ndarray) -> np.ndarray:
        """
        将BGR图像转换为HSV颜色空间
        
        Args:
            image: BGR格式图像
            
        Returns:
            HSV格式图像
        """
        if image is None:
            raise ValueError("输入图像不能为空")
        
        try:
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            logger.debug(f"图像转换为HSV成功，尺寸: {hsv_image.shape}")
            return hsv_image
        except Exception as e:
            logger.error(f"BGR转HSV失败: {e}")
            raise
    
    def apply_threshold(self, image: np.ndarray, threshold: Dict[str, Tuple[int, int]]) -> np.ndarray:
        """
        应用HSV阈值处理
        
        Args:
            image: HSV格式图像
            threshold: HSV阈值字典 {'h': (min, max), 's': (min, max), 'v': (min, max)}
            
        Returns:
            二值化掩码图像
        """
        if image is None:
            raise ValueError("输入图像不能为空")
        
        # 提取阈值范围
        h_range = threshold.get('h', (0, 179))
        s_range = threshold.get('s', (0, 255))
        v_range = threshold.get('v', (0, 255))
        
        # 处理色相通道的循环特性
        h_min, h_max = h_range
        s_min, s_max = s_range
        v_min, v_max = v_range
        
        if h_min <= h_max:
            # 正常情况
            lower_bound = np.array([h_min, s_min, v_min])
            upper_bound = np.array([h_max, s_max, v_max])
            mask = cv2.inRange(image, lower_bound, upper_bound)
        else:
            # 色相跨越0点的情况（如红色: 170-10）
            lower_bound1 = np.array([h_min, s_min, v_min])
            upper_bound1 = np.array([179, s_max, v_max])
            lower_bound2 = np.array([0, s_min, v_min])
            upper_bound2 = np.array([h_max, s_max, v_max])
            
            mask1 = cv2.inRange(image, lower_bound1, upper_bound1)
            mask2 = cv2.inRange(image, lower_bound2, upper_bound2)
            mask = cv2.bitwise_or(mask1, mask2)
        
        # 形态学操作去除噪声
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        self.last_mask = mask
        logger.debug(f"阈值处理完成，掩码像素数: {np.sum(mask > 0)}")
        
        return mask
    
    def create_mask(self, image: np.ndarray, threshold: Dict[str, Tuple[int, int]]) -> np.ndarray:
        """
        创建颜色掩码
        
        Args:
            image: 输入图像 (BGR格式)
            threshold: HSV阈值
            
        Returns:
            掩码图像
        """
        # 预处理
        processed_image = self.preprocess(image)
        
        # 转换为HSV
        hsv_image = self.convert_to_hsv(processed_image)
        
        # 应用阈值
        mask = self.apply_threshold(hsv_image, threshold)
        
        self.last_processed_image = processed_image
        
        return mask
    
    def calculate_histogram(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        计算HSV直方图
        
        Args:
            image: HSV格式图像
            
        Returns:
            直方图字典 {'h': hist_h, 's': hist_s, 'v': hist_v}
        """
        if image is None:
            raise ValueError("输入图像不能为空")
        
        try:
            # 分离HSV通道
            h, s, v = cv2.split(image)
            
            # 计算各通道直方图
            hist_h = cv2.calcHist([h], [0], None, [180], [0, 180])
            hist_s = cv2.calcHist([s], [0], None, [256], [0, 256])
            hist_v = cv2.calcHist([v], [0], None, [256], [0, 256])
            
            histogram = {
                'h': hist_h.flatten(),
                's': hist_s.flatten(),
                'v': hist_v.flatten()
            }
            
            self.last_histogram = histogram
            logger.debug("直方图计算完成")
            
            return histogram
            
        except Exception as e:
            logger.error(f"直方图计算失败: {e}")
            raise
    
    def get_mask_statistics(self, mask: np.ndarray, image_shape: Tuple[int, int]) -> Dict[str, Any]:
        """
        获取掩码统计信息
        
        Args:
            mask: 掩码图像
            image_shape: 原图像尺寸 (height, width)
            
        Returns:
            统计信息字典
        """
        if mask is None:
            return {'pixel_count': 0, 'coverage_ratio': 0.0, 'contour_count': 0}
        
        # 像素数量
        pixel_count = np.sum(mask > 0)
        
        # 覆盖率
        total_pixels = image_shape[0] * image_shape[1]
        coverage_ratio = pixel_count / total_pixels if total_pixels > 0 else 0.0
        
        # 轮廓数量
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour_count = len(contours)
        
        return {
            'pixel_count': int(pixel_count),
            'coverage_ratio': float(coverage_ratio),
            'contour_count': contour_count,
            'image_size': image_shape
        }
    
    def apply_mask_to_image(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        将掩码应用到图像上
        
        Args:
            image: 原图像
            mask: 掩码图像
            
        Returns:
            应用掩码后的图像
        """
        if image is None or mask is None:
            return image
        
        # 创建彩色掩码
        mask_colored = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
        
        # 混合原图像和掩码
        result = cv2.addWeighted(image, 0.7, mask_colored, 0.3, 0)
        
        return result
    
    def resize_image(self, image: np.ndarray, max_width: int = 640, max_height: int = 480) -> np.ndarray:
        """
        调整图像大小以适应显示
        
        Args:
            image: 输入图像
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            调整大小后的图像
        """
        if image is None:
            return None
        
        height, width = image.shape[:2]
        
        # 计算缩放比例
        scale_w = max_width / width
        scale_h = max_height / height
        scale = min(scale_w, scale_h, 1.0)  # 不放大图像
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"图像从 {width}x{height} 调整为 {new_width}x{new_height}")
            return resized
        
        return image 