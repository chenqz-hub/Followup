"""
测试 - 配置管理
"""

import pytest
import os
from src.config import Config


class TestConfig:
    """配置管理测试"""
    
    def test_load_config(self):
        """测试加载配置文件"""
        config = Config('config/config.yaml')
        assert config is not None
    
    def test_get_config_value(self):
        """测试获取配置值"""
        config = Config('config/config.yaml')
        
        source_type = config.get('data_source.type')
        assert source_type is not None
    
    def test_get_nested_config(self):
        """测试获取嵌套配置"""
        config = Config('config/config.yaml')
        
        events = config.get_nested('events')
        assert 'types' in events
    
    def test_config_with_default_value(self):
        """测试使用默认值"""
        config = Config('config/config.yaml')
        
        value = config.get('nonexistent.key', 'default_value')
        assert value == 'default_value'
    
    def test_config_validation(self):
        """测试配置验证"""
        config = Config('config/config.yaml')
        assert config.validate() is True
    
    def test_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError):
            Config('nonexistent/config.yaml')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
