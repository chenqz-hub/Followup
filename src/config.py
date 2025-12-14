"""
配置管理模块
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """
    配置管理类 - 从YAML文件加载和管理配置
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """从YAML文件加载配置"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值 (支持嵌套键，用点号分隔)
        
        Args:
            key: 配置键 (如 "data_source.type")
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_nested(self, section: str) -> Dict[str, Any]:
        """
        获取嵌套配置段落
        
        Args:
            section: 配置段落名称
            
        Returns:
            配置字典
        """
        return self._config.get(section, {})
    
    def validate(self) -> bool:
        """验证配置的完整性和有效性"""
        required_sections = ['data_source', 'patient', 'events', 'output', 'logging']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"缺少必要的配置段落: {section}")
        
        # 验证事件类型
        events_config = self._config.get('events', {})
        event_types = events_config.get('types', {})
        if not event_types:
            raise ValueError("未定义任何事件类型")
        
        return True
    
    def __repr__(self) -> str:
        """配置的字符串表示"""
        return f"<Config: {self.config_path}>"
