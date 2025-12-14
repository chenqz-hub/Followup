"""
纵向随访数据处理示例 - 展示如何处理多时间点的CAD患者随访数据
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 设置工作目录为项目根目录
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root / 'src'))

# 临时修补相对导入
import types
old_import = __builtins__.__import__

def custom_import(name, *args, **kwargs):
    """自定义导入函数，处理相对导入"""
    if name.startswith('.'):
        # 这是相对导入，需要处理
        # 对于本示例，我们不需要处理，因为我们已经在sys.path中设置了src目录
        pass
    return old_import(name, *args, **kwargs)

# 现在导入模块
from config import Config
from logger import setup_logger
from longitudinal_importer import LongitudinalDataImporter
from longitudinal_processor import LongitudinalEventProcessor
from data_exporter import DataExporter
from longitudinal_models import LongitudinalFollowupRecord

# 将在main函数中设置日志


def main():
    """主处理流程"""
    
    # 设置日志
    logger = setup_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("纵向CAD患者随访数据处理")
    logger.info("=" * 60)
    
    # 1. 加载配置
    logger.info("步骤1: 加载配置文件...")
    config = Config()
    logger.info(f"  配置已加载")
    
    # 2. 初始化导入器
    logger.info("步骤2: 初始化导入器...")
    importer = LongitudinalDataImporter()
    
    # 3. 加载Excel文件
    template_file = r"d:\git\Followup\data\extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx"
    logger.info(f"步骤3: 加载Excel文件...")
    logger.info(f"  文件路径: {template_file}")
    
    if not importer.load_excel_file(template_file):
        logger.error("加载Excel文件失败")
        return False
    
    # 4. 导入纵向数据
    logger.info("步骤4: 导入并合并纵向数据...")
    longitudinal_records = importer.import_longitudinal_data()
    logger.info(f"  成功导入{len(longitudinal_records)}条纵向患者记录")
    
    if not longitudinal_records:
        logger.error("未导入任何数据")
        return False
    
    # 显示前几条记录的摘要
    logger.info("  前5条记录摘要:")
    for i, record in enumerate(longitudinal_records[:5], 1):
        logger.info(
            f"    {i}. 患者{record.patient_id}: "
            f"入组{record.enrollment_date}, "
            f"最晚随访{record.latest_followup_date} ({record.latest_followup_months}月), "
            f"{len(record.time_points)}个时间点"
        )
    
    # 5. 初始化事件处理器
    logger.info("步骤5: 初始化事件处理器...")
    processor = LongitudinalEventProcessor()
    
    # 6. 处理事件
    logger.info("步骤6: 识别事件并计算指标...")
    followup_records = processor.process_batch(longitudinal_records)
    logger.info(f"  成功处理{len(followup_records)}条随访记录")
    
    # 统计事件分布
    logger.info("  事件分布统计:")
    event_counts = {}
    for record in followup_records:
        event_type = record.first_event_type or 'no_event'
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    for event_type, count in sorted(event_counts.items()):
        percentage = (count / len(followup_records)) * 100
        logger.info(f"    {event_type}: {count} ({percentage:.1f}%)")
    
    # 7. 导出结果
    logger.info("步骤7: 导出结果...")
    exporter = DataExporter()
    
    # 转换为字典列表用于导出
    output_data = [record.to_flattened_dict() for record in followup_records]
    
    # 输出文件路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_longitudinal_followup_{timestamp}.xlsx"
    output_path = Path(__file__).parent / "output" / output_file
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 导出到Excel
    try:
        exporter.to_excel(str(output_path), output_data)
        logger.info(f"  结果已导出到: {output_path}")
        logger.info(f"  导出{len(output_data)}条记录")
    except Exception as e:
        logger.error(f"导出失败: {e}")
        return False
    
    # 8. 显示样本数据
    logger.info("步骤8: 样本输出数据:")
    if followup_records:
        sample = followup_records[0]
        logger.info(f"  患者{sample.patient_id}:")
        logger.info(f"    入组日期: {sample.enrollment_date}")
        logger.info(f"    最晚随访日期: {sample.latest_followup_date}")
        logger.info(f"    距入组天数: {sample.days_to_latest_followup}")
        logger.info(f"    首次事件类型: {sample.first_event_type}")
        logger.info(f"    首次事件日期: {sample.first_event_date}")
        logger.info(f"    首次事件距入组天数: {sample.days_to_first_event}")
        logger.info(f"    随访状态: {sample.total_followup_status}")
    
    logger.info("=" * 60)
    logger.info("处理完成!")
    logger.info("=" * 60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
