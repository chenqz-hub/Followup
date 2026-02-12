"""
Follow-up Data Processing Tool
用于从冠心病数据库提取患者随访信息的工具
"""

__version__ = "1.0.0"
__author__ = "CAD Research Team"

from .logger import setup_logger
from .config import Config
from .data_models import PatientRecord, FollowupRecord, EventInfo

__all__ = [
    "setup_logger",
    "Config",
    "PatientRecord",
    "FollowupRecord",
    "EventInfo",
]
