"""
示例脚本3：完整流程示例
从数据导入到结果导出的完整工作流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.logger import setup_logger
from src.data_importer import DataImporter
from src.event_processor import EventProcessor
from src.data_exporter import FollowupExporter


def example_complete_workflow():
    """
    完整工作流程示例
    """
    print("\n" + "="*60)
    print("示例 3: 完整工作流程")
    print("="*60)
    
    try:
        # 1. 加载配置
        print("\n第1步: 加载配置...")
        config = Config('config/config.yaml')
        config.validate()
        print(f"  ✓ 配置有效")
        
        # 2. 初始化日志
        print("\n第2步: 初始化日志系统...")
        logger = setup_logger(
            'complete_workflow',
            log_dir=config.get('logging.log_dir', 'logs'),
            level=config.get('logging.level', 'INFO')
        )
        print(f"  ✓ 日志系统已初始化")
        
        # 3. 导入数据
        print("\n第3步: 导入患者数据...")
        source_type = config.get('data_source.type')
        source_path = config.get('data_source.connection_string')
        print(f"  数据源: {source_type} ({source_path})")
        
        patients = DataImporter.import_from_config(config)
        print(f"  ✓ 成功导入 {len(patients)} 条患者记录")
        
        if not patients:
            print("  ⚠ 未导入任何数据，请检查数据源配置")
            return
        
        # 4. 处理事件
        print("\n第4步: 处理患者事件...")
        processor = EventProcessor(config)
        
        followup_records = []
        for i, patient in enumerate(patients):
            followup = processor.process_patient(patient)
            followup_records.append(followup)
            
            if (i + 1) % 100 == 0 or i == 0:
                print(f"  已处理 {i + 1}/{len(patients)} 条记录", end='\r')
        
        print(f"  ✓ 已处理全部 {len(followup_records)} 条患者记录        ")
        
        # 5. 数据统计
        print("\n第5步: 数据统计...")
        patients_with_events = sum(
            1 for r in followup_records if r.first_event_type
        )
        print(f"  总患者数: {len(followup_records)}")
        print(f"  有事件患者: {patients_with_events}")
        print(f"  无事件患者: {len(followup_records) - patients_with_events}")
        
        # 事件类型统计
        event_types = {}
        for record in followup_records:
            if record.first_event_type:
                event_types[record.first_event_type] = \
                    event_types.get(record.first_event_type, 0) + 1
        
        if event_types:
            print(f"  事件类型分布:")
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {event_type}: {count}")
        
        # 6. 导出结果
        print("\n第6步: 导出随访数据...")
        exporter = FollowupExporter(config)
        summary = exporter.export_with_summary(followup_records)
        print(f"  ✓ 数据已导出")
        print(f"  输出文件: {summary['output_file']}")
        
        # 7. 显示完整摘要
        print("\n" + "="*60)
        print("处理摘要")
        print("="*60)
        print(f"输入患者数:        {summary['total_patients']}")
        print(f"有事件患者数:      {summary['patients_with_events']}")
        print(f"无事件患者数:      {summary['patients_without_events']}")
        print(f"总事件数:          {summary['total_events']}")
        print(f"输出文件:          {summary['output_file']}")
        print(f"处理时间:          {summary['export_timestamp']}")
        
        print("\n" + "="*60)
        print("✓ 示例 3 完成")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    example_complete_workflow()
