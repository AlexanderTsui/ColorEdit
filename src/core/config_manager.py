#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
实现HSV阈值配置的保存、加载和管理
"""

import json
import os
from typing import Dict, Tuple, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: str = "configs"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件存储目录
        """
        self.config_dir = config_dir
        self.ensure_config_dir()
        
        # 默认HSV阈值
        self.default_threshold = {
            'h': (0, 179),
            's': (0, 255),
            'v': (0, 255)
        }
        
        # 颜色预设
        self.color_presets = {
            '红色': {
                'h': (0, 10),
                's': (100, 255),
                'v': (50, 255),
                'description': '检测红色物体'
            },
            '绿色': {
                'h': (40, 70),
                's': (100, 255),
                'v': (50, 255),
                'description': '检测绿色物体'
            },
            '蓝色': {
                'h': (100, 130),
                's': (100, 255),
                'v': (50, 255),
                'description': '检测蓝色物体'
            },
            '黄色': {
                'h': (20, 30),
                's': (100, 255),
                'v': (100, 255),
                'description': '检测黄色物体'
            },
            '橙色': {
                'h': (10, 20),
                's': (100, 255),
                'v': (100, 255),
                'description': '检测橙色物体'
            },
            '紫色': {
                'h': (130, 160),
                's': (100, 255),
                'v': (50, 255),
                'description': '检测紫色物体'
            },
            '青色': {
                'h': (80, 100),
                's': (100, 255),
                'v': (50, 255),
                'description': '检测青色物体'
            },
            '粉色': {
                'h': (160, 180),
                's': (100, 255),
                'v': (100, 255),
                'description': '检测粉色物体'
            }
        }
    
    def ensure_config_dir(self) -> None:
        """确保配置目录存在"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            logger.info(f"创建配置目录: {self.config_dir}")
    
    def save_threshold_config(self, threshold: Dict[str, Tuple[int, int]], 
                            name: str = None, description: str = "") -> str:
        """
        保存HSV阈值配置
        
        Args:
            threshold: HSV阈值字典
            name: 配置名称，如果为None则自动生成
            description: 配置描述
            
        Returns:
            配置文件路径
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"threshold_config_{timestamp}"
        
        config_data = {
            'name': name,
            'description': description,
            'threshold': threshold,
            'created_time': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        filename = f"{name}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"阈值配置已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def load_threshold_config(self, filepath: str) -> Dict[str, Any]:
        """
        加载HSV阈值配置
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            配置数据字典
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置格式
            if not self.validate_config(config_data):
                raise ValueError("配置文件格式无效")
            
            logger.info(f"阈值配置已加载: {filepath}")
            return config_data
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """
        验证配置数据格式
        
        Args:
            config_data: 配置数据
            
        Returns:
            是否有效
        """
        required_keys = ['threshold']
        
        # 检查必需字段
        for key in required_keys:
            if key not in config_data:
                logger.error(f"配置缺少必需字段: {key}")
                return False
        
        # 检查阈值格式
        threshold = config_data['threshold']
        required_channels = ['h', 's', 'v']
        
        for channel in required_channels:
            if channel not in threshold:
                logger.error(f"阈值缺少通道: {channel}")
                return False
            
            if not isinstance(threshold[channel], (list, tuple)) or len(threshold[channel]) != 2:
                logger.error(f"通道 {channel} 格式错误")
                return False
            
            min_val, max_val = threshold[channel]
            if not isinstance(min_val, int) or not isinstance(max_val, int):
                logger.error(f"通道 {channel} 值必须为整数")
                return False
        
        return True
    
    def get_config_list(self) -> List[Dict[str, Any]]:
        """
        获取配置文件列表
        
        Returns:
            配置文件信息列表
        """
        configs = []
        
        try:
            for filename in os.listdir(self.config_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.config_dir, filename)
                    try:
                        config_data = self.load_threshold_config(filepath)
                        configs.append({
                            'filepath': filepath,
                            'filename': filename,
                            'name': config_data.get('name', filename),
                            'description': config_data.get('description', ''),
                            'created_time': config_data.get('created_time', ''),
                            'threshold': config_data['threshold']
                        })
                    except Exception as e:
                        logger.warning(f"跳过无效配置文件 {filename}: {e}")
            
            # 按创建时间排序
            configs.sort(key=lambda x: x.get('created_time', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"获取配置列表失败: {e}")
        
        return configs
    
    def delete_config(self, filepath: str) -> bool:
        """
        删除配置文件
        
        Args:
            filepath: 配置文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"配置文件已删除: {filepath}")
                return True
            else:
                logger.warning(f"配置文件不存在: {filepath}")
                return False
        except Exception as e:
            logger.error(f"删除配置文件失败: {e}")
            return False
    
    def get_color_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        获取颜色预设
        
        Returns:
            颜色预设字典
        """
        return self.color_presets.copy()
    
    def add_color_preset(self, name: str, threshold: Dict[str, Tuple[int, int]], 
                        description: str = "") -> None:
        """
        添加颜色预设
        
        Args:
            name: 预设名称
            threshold: HSV阈值
            description: 描述
        """
        self.color_presets[name] = {
            'h': threshold['h'],
            's': threshold['s'],
            'v': threshold['v'],
            'description': description
        }
        
        # 保存预设到文件
        self.save_presets()
        logger.info(f"颜色预设已添加: {name}")
    
    def remove_color_preset(self, name: str) -> bool:
        """
        移除颜色预设
        
        Args:
            name: 预设名称
            
        Returns:
            是否移除成功
        """
        if name in self.color_presets:
            del self.color_presets[name]
            self.save_presets()
            logger.info(f"颜色预设已移除: {name}")
            return True
        return False
    
    def save_presets(self) -> None:
        """保存颜色预设到文件"""
        presets_file = os.path.join(self.config_dir, "color_presets.json")
        
        try:
            with open(presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.color_presets, f, ensure_ascii=False, indent=2)
            logger.debug("颜色预设已保存")
        except Exception as e:
            logger.error(f"保存颜色预设失败: {e}")
    
    def load_presets(self) -> None:
        """从文件加载颜色预设"""
        presets_file = os.path.join(self.config_dir, "color_presets.json")
        
        if os.path.exists(presets_file):
            try:
                with open(presets_file, 'r', encoding='utf-8') as f:
                    loaded_presets = json.load(f)
                self.color_presets.update(loaded_presets)
                logger.info("颜色预设已加载")
            except Exception as e:
                logger.error(f"加载颜色预设失败: {e}")
    
    def export_config(self, threshold: Dict[str, Tuple[int, int]], 
                     export_path: str, name: str = None, description: str = "") -> None:
        """
        导出配置到指定路径
        
        Args:
            threshold: HSV阈值
            export_path: 导出路径
            name: 配置名称
            description: 配置描述
        """
        if name is None:
            name = os.path.splitext(os.path.basename(export_path))[0]
        
        config_data = {
            'name': name,
            'description': description,
            'threshold': threshold,
            'exported_time': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已导出: {export_path}")
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
    
    def get_default_threshold(self) -> Dict[str, Tuple[int, int]]:
        """获取默认阈值"""
        return self.default_threshold.copy()
    
    def reset_to_defaults(self) -> Dict[str, Tuple[int, int]]:
        """重置为默认阈值"""
        logger.info("阈值已重置为默认值")
        return self.get_default_threshold() 