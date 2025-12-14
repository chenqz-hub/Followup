"""
主程序入口
"""

import logging
import sys
from pathlib import Path
from config import Config
from logger import setup_logger
from data_importer import DataImporter
from event_processor import EventProcessor
from data_exporter import FollowupExporter


def main(config_path: str = "config/config.yaml") -> int:
    """
    主程序
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        返回码 (0: 成功, 1: 失败)
    """
    try:
        # 加载配置
        config = Config(config_path)
        config.validate()
        
        # 设置日志
        log_config = config.get_nested('logging')
        logger = setup_logger(
            name='followup_processor',
            log_dir=log_config.get('log_dir', 'logs'),
            level=log_config.get('level', 'INFO'),
            max_bytes=log_config.get('max_log_size', 10485760),
            backup_count=log_config.get('backup_count', 5)
        )
        
        logger.info("=" * 50)
        logger.info("随访数据处理工具启动")
        logger.info(f"配置文件: {config_path}")
        logger.info("=" * 50)
        
        # 导入数据
        logger.info("正在导入患者数据...")
        patients = DataImporter.import_from_config(config)
        logger.info(f"成功导入 {len(patients)} 条患者记录")
        
        if not patients:
            logger.warning("未导入任何患者数据，程序退出")
            return 1
        
        # 处理事件
        logger.info("正在处理患者事件...")
        event_processor = EventProcessor(config)
        followup_records = [
            event_processor.process_patient(patient)
            for patient in patients
        ]
        logger.info(f"成功处理 {len(followup_records)} 条患者记录")
        
        # 导出数据
        logger.info("正在导出随访数据...")
        exporter = FollowupExporter(config)
        summary = exporter.export_with_summary(followup_records)
        
        logger.info("=" * 50)
        logger.info("随访数据处理工具完成")
        logger.info("=" * 50)
        
        return 0
    
    except Exception as e:
        logging.error(f"程序执行出错: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    sys.exit(main(config_file))
