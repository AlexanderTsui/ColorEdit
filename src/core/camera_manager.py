#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头管理模块
实现摄像头的启动、停止、切换等功能
"""

import cv2
import threading
import time
import logging
from typing import Optional, Callable, List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class CameraManager:
    """摄像头管理器类"""
    
    def __init__(self, frame_callback: Optional[Callable] = None):
        """
        初始化摄像头管理器
        
        Args:
            frame_callback: 帧回调函数，用于处理每一帧图像
        """
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.current_device_id = 0
        self.frame_callback = frame_callback
        self.capture_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        self.fps = 30
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        self.error_message = ""
        
        # 摄像头设置
        self.camera_settings = {
            'width': 640,
            'height': 480,
            'fps': 30
        }
    
    def get_available_cameras(self) -> List[Dict[str, Any]]:
        """
        获取可用摄像头列表
        
        Returns:
            摄像头信息列表
        """
        cameras = []
        
        # 测试前10个设备ID
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 获取摄像头信息
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                cameras.append({
                    'id': i,
                    'name': f'摄像头 {i}',
                    'width': int(width),
                    'height': int(height),
                    'fps': int(fps)
                })
                
                cap.release()
            else:
                break
        
        logger.info(f"发现 {len(cameras)} 个可用摄像头")
        return cameras
    
    def start_camera(self, device_id: int = 0) -> bool:
        """
        启动摄像头
        
        Args:
            device_id: 设备ID
            
        Returns:
            是否启动成功
        """
        if self.is_active:
            logger.warning("摄像头已在运行")
            return True
        
        try:
            # 创建VideoCapture对象
            self.cap = cv2.VideoCapture(device_id)
            
            if not self.cap.isOpened():
                self.error_message = f"无法打开摄像头设备 {device_id}"
                logger.error(self.error_message)
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_settings['width'])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_settings['height'])
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_settings['fps'])
            
            # 设置缓冲区大小（减少延迟）
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.current_device_id = device_id
            self.is_active = True
            self.error_message = ""
            
            # 启动捕获线程
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info(f"摄像头 {device_id} 启动成功")
            return True
            
        except Exception as e:
            self.error_message = f"摄像头启动失败: {str(e)}"
            logger.error(self.error_message)
            return False
    
    def stop_camera(self) -> None:
        """停止摄像头"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # 等待捕获线程结束
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # 释放摄像头资源
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("摄像头已停止")
    
    def switch_camera(self, device_id: int) -> bool:
        """
        切换摄像头
        
        Args:
            device_id: 目标设备ID
            
        Returns:
            是否切换成功
        """
        if device_id == self.current_device_id:
            return True
        
        # 停止当前摄像头
        was_active = self.is_active
        self.stop_camera()
        
        # 启动新摄像头
        if was_active:
            return self.start_camera(device_id)
        
        self.current_device_id = device_id
        return True
    
    def _capture_loop(self) -> None:
        """摄像头捕获循环（在独立线程中运行）"""
        frame_interval = 1.0 / self.fps
        last_frame_time = time.time()
        
        while self.is_active and self.cap and self.cap.isOpened():
            try:
                # 控制帧率
                current_time = time.time()
                elapsed = current_time - last_frame_time
                
                if elapsed < frame_interval:
                    time.sleep(frame_interval - elapsed)
                    continue
                
                # 读取帧
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("无法读取摄像头帧")
                    continue
                
                # 更新FPS统计
                self._update_fps_stats()
                
                # 调用帧回调函数
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        logger.error(f"帧回调函数执行失败: {e}")
                
                last_frame_time = current_time
                
            except Exception as e:
                logger.error(f"摄像头捕获循环错误: {e}")
                break
        
        logger.debug("摄像头捕获循环已退出")
    
    def _update_fps_stats(self) -> None:
        """更新FPS统计"""
        self.frame_count += 1
        current_time = time.time()
        
        # 每秒更新一次FPS
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def get_camera_info(self) -> Dict[str, Any]:
        """
        获取当前摄像头信息
        
        Returns:
            摄像头信息字典
        """
        if not self.cap or not self.is_active:
            return {}
        
        try:
            info = {
                'device_id': self.current_device_id,
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
                'current_fps': self.current_fps,
                'is_active': self.is_active
            }
            return info
        except Exception as e:
            logger.error(f"获取摄像头信息失败: {e}")
            return {}
    
    def set_camera_settings(self, settings: Dict[str, Any]) -> bool:
        """
        设置摄像头参数
        
        Args:
            settings: 设置字典
            
        Returns:
            是否设置成功
        """
        try:
            # 更新内部设置
            self.camera_settings.update(settings)
            
            if self.cap and self.is_active:
                # 应用设置到摄像头
                if 'width' in settings:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings['width'])
                if 'height' in settings:
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings['height'])
                if 'fps' in settings:
                    self.cap.set(cv2.CAP_PROP_FPS, settings['fps'])
                    self.fps = settings['fps']
            
            logger.info(f"摄像头设置已更新: {settings}")
            return True
            
        except Exception as e:
            logger.error(f"设置摄像头参数失败: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        手动捕获一帧图像
        
        Returns:
            捕获的图像，如果失败返回None
        """
        if not self.cap or not self.is_active:
            return None
        
        try:
            with self.lock:
                ret, frame = self.cap.read()
                if ret:
                    return frame
                else:
                    logger.warning("捕获帧失败")
                    return None
        except Exception as e:
            logger.error(f"手动捕获帧错误: {e}")
            return None
    
    def get_error_message(self) -> str:
        """获取错误信息"""
        return self.error_message
    
    def is_camera_active(self) -> bool:
        """检查摄像头是否处于活动状态"""
        return self.is_active
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop_camera() 