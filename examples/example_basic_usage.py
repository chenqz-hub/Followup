"""
示例脚本1：基本使用示例
演示如何使用跟踪数据处理工具的基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.logger import setup_logger
from src.data_importer import DataImporter
from src.event_processor import EventProcessor
from src.data_exporter import FollowupExporter


def example_basic_usage():
    """
    基本使用示例
    """
    print("\n" + "="*60)
    print("示例 1: 基本使用")
    print("="*60)
    
    try:
        # 1. 加载配置
        print("\n1. 加载配置...")
        config = Config('config/config.yaml')
        print(f"   ✓ 配置加载成功")
        
        # 2. 设置日志
        print("\n2. 设置日志...")
        logger = setup_logger('example_basic')
        print(f"   ✓ 日志系统已初始化")
        
        # 3. 导入数据
        print("\n3. 导入患者数据...")
        print(f"   使用数据源: {config.get('data_source.type')}")
        patients = DataImporter.import_from_config(config)
        print(f"   ✓ 成功导入 {len(patients)} 条患者记录")
        
        if patients:
            print(f"   示例患者: ID={patients[0].patient_id}, "
                  f"入组日期={patients[0].enrollment_date}")
        
        # 4. 处理事件
        print("\n4. 处理患者事件...")
        processor = EventProcessor(config)
        followup_records = [
            processor.process_patient(patient)
            for patient in patients[:5]  # 仅处理前5个患者作为示例
        ]
        print(f"   ✓ 成功处理 {len(followup_records)} 条患者记录")
        
        # 5. 显示结果示例
        print("\n5. 处理结果示例:")
        for record in followup_records[:3]:
            print(f"\n   患者 {record.patient_id}:")
            print(f"     入组日期: {record.enrollment_date}")
            print(f"     首次事件: {record.first_event_type}")
            print(f"     首次事件日期: {record.first_event_date}")
            print(f"     天数差异: {record.days_to_first_event}")
            print(f"     总事件数: {record.event_count}")
        
        print("\n" + "="*60)
        print("✓ 示例 1 完成")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    example_basic_usage()
