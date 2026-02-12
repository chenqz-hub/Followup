"""配置模块测试"""

import pytest
from pathlib import Path
import tempfile
import yaml
from src.config import Config


class TestConfig:
    """Config类测试"""

    def test_load_from_file(self, sample_config_dict):
        """测试从文件加载配置"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config_dict, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.get("data_source.type") == "csv"
            assert config.get("patient.patient_id_field") == "patient_id"
        finally:
            Path(temp_path).unlink()

    def test_get_nested_value(self, sample_config_dict):
        """测试获取嵌套配置值"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config_dict, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.get("events.types.death.priority") == 1
        finally:
            Path(temp_path).unlink()

    def test_get_with_default(self, sample_config_dict):
        """测试使用默认值"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config_dict, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            assert config.get("nonexistent.key", "default") == "default"
        finally:
            Path(temp_path).unlink()

    def test_validate_config(self, sample_config_dict):
        """测试配置验证"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config_dict, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            # 应该不抛出异常
            assert config.validate() == True
        finally:
            Path(temp_path).unlink()

    def test_validate_missing_required_field(self):
        """测试缺少必需字段时的验证"""
        invalid_config = {"data_source": {}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(invalid_config, f)
            temp_path = f.name

        try:
            config = Config(temp_path)
            with pytest.raises(ValueError):
                config.validate()
        finally:
            Path(temp_path).unlink()
