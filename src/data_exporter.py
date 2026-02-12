"""
数据导出模块
支持导出为CSV、Excel等格式
"""

import logging
import os
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
from abc import ABC, abstractmethod
from .config import Config
from .data_models import FollowupRecord

logger = logging.getLogger(__name__)


class DataExporter(ABC):
    """数据导出器抽象基类"""

    @abstractmethod
    def export(self, records: List[FollowupRecord], output_path: str) -> str:
        """
        导出数据

        Args:
            records: 随访记录列表
            output_path: 输出文件路径

        Returns:
            实际生成的文件路径
        """
        pass


class CSVExporter(DataExporter):
    """CSV格式导出器"""

    def export(self, records: List[FollowupRecord], output_path: str) -> str:
        """
        导出为CSV文件

        Args:
            records: 随访记录列表
            output_path: 输出文件路径

        Returns:
            实际生成的文件路径
        """
        try:
            # 转换记录为字典列表
            data = [record.to_flattened_dict() for record in records]

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 创建输出目录
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存为CSV
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            logger.info(f"成功导出 {len(records)} 条记录到CSV文件: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"导出CSV文件失败: {e}")
            raise


class ExcelExporter(DataExporter):
    """Excel格式导出器"""

    def export(self, records: List[FollowupRecord], output_path: str) -> str:
        """
        导出为Excel文件

        Args:
            records: 随访记录列表
            output_path: 输出文件路径

        Returns:
            实际生成的文件路径
        """
        try:
            # 转换记录为字典列表
            data = [record.to_flattened_dict() for record in records]

            # 创建DataFrame
            df = pd.DataFrame(data)

            # 创建输出目录
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # 保存为Excel
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Follow-up Data", index=False)

                # 获取工作表并调整列宽
                worksheet = writer.sheets["Follow-up Data"]
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column)
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

            logger.info(f"成功导出 {len(records)} 条记录到Excel文件: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"导出Excel文件失败: {e}")
            raise


class FollowupExporter:
    """随访数据导出管理器"""

    def __init__(self, config: Config):
        """
        初始化导出器

        Args:
            config: 配置对象
        """
        self.config = config
        self.output_dir = config.get("output.output_dir", "output")
        self.output_format = config.get("output.format", "excel")
        self.filename_prefix = config.get("output.filename_prefix", "followup_data")

    def export(self, records: List[FollowupRecord]) -> str:
        """
        导出随访数据

        Args:
            records: 随访记录列表

        Returns:
            生成的文件路径
        """
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.output_format.lower() == "csv":
            filename = f"{self.filename_prefix}_{timestamp}.csv"
            exporter = CSVExporter()
        elif self.output_format.lower() == "excel":
            filename = f"{self.filename_prefix}_{timestamp}.xlsx"
            exporter = ExcelExporter()
        else:
            raise ValueError(f"不支持的输出格式: {self.output_format}")

        output_path = os.path.join(self.output_dir, filename)

        return exporter.export(records, output_path)

    def export_with_summary(self, records: List[FollowupRecord]) -> Dict[str, Any]:
        """
        导出数据并生成统计摘要

        Args:
            records: 随访记录列表

        Returns:
            包含文件路径和统计信息的字典
        """
        output_path = self.export(records)

        # 生成统计摘要
        total_patients = len(records)
        patients_with_events = sum(1 for r in records if r.first_event_type)
        total_events = sum(r.event_count for r in records)

        # 按事件类型统计
        event_type_counts: Dict[str, int] = {}
        for record in records:
            if record.first_event_type:
                event_type_counts[record.first_event_type] = (
                    event_type_counts.get(record.first_event_type, 0) + 1
                )

        summary = {
            "output_file": output_path,
            "total_patients": total_patients,
            "patients_with_events": patients_with_events,
            "patients_without_events": total_patients - patients_with_events,
            "total_events": total_events,
            "event_type_distribution": event_type_counts,
            "export_timestamp": datetime.now().isoformat(),
        }

        logger.info(f"\n=== 导出摘要 ===")
        logger.info(f"文件路径: {output_path}")
        logger.info(f"总患者数: {total_patients}")
        logger.info(f"有事件患者数: {patients_with_events}")
        logger.info(f"无事件患者数: {total_patients - patients_with_events}")
        logger.info(f"总事件数: {total_events}")
        logger.info(f"事件类型分布: {event_type_counts}")

        return summary
