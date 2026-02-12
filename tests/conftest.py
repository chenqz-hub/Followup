"""pytest配置文件"""

import sys
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from datetime import date


@pytest.fixture
def sample_config_dict():
    """示例配置字典"""
    return {
        "data_source": {"type": "csv", "connection_string": "test.csv"},
        "patient": {"enrollment_date_field": "enrollment_date", "patient_id_field": "patient_id"},
        "events": {
            "types": {
                "death": {"field_names": ["death_date"], "priority": 1},
                "mi": {"field_names": ["mi_date"], "priority": 2},
            }
        },
        "output": {"format": "csv", "file_path": "output/test.csv"},
        "logging": {"level": "INFO", "log_dir": "logs"},
    }


@pytest.fixture
def sample_patient_data():
    """示例患者数据"""
    return {
        "patient_id": "P001",
        "enrollment_date": date(2020, 1, 1),
        "death_date": date(2021, 6, 15),
        "mi_date": None,
    }
