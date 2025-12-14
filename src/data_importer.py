"""
数据导入模块
支持从多种数据源导入数据
"""

import logging
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod
from config import Config
from data_models import PatientRecord


logger = logging.getLogger(__name__)


class DataSource(ABC):
    """数据源抽象基类"""
    
    @abstractmethod
    def load_data(self) -> List[PatientRecord]:
        """加载数据并返回患者记录列表"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭数据源连接"""
        pass


class SQLiteDataSource(DataSource):
    """SQLite数据源"""
    
    def __init__(self, connection_string: str):
        """
        初始化SQLite数据源
        
        Args:
            connection_string: 数据库文件路径
        """
        self.connection_string = connection_string
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.connection_string)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"连接到SQLite数据库: {self.connection_string}")
        except sqlite3.Error as e:
            logger.error(f"连接SQLite数据库失败: {e}")
            raise
    
    def load_data(self, table_name: str = "patients") -> List[PatientRecord]:
        """
        从SQLite数据库加载患者数据
        
        Args:
            table_name: 表名称
            
        Returns:
            患者记录列表
        """
        if self.conn is None:
            self.connect()
        
        try:
            # 查询所有数据
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            
            # 获取列名
            columns = [description[0] for description in cursor.description]
            
            # 转换为PatientRecord
            records: List[PatientRecord] = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                
                try:
                    # 提取患者ID和入组日期
                    patient_id = row_dict.get('patient_id', row_dict.get('id', ''))
                    enrollment_date = row_dict.get(
                        'enrollment_date',
                        row_dict.get('enrollmentDate', row_dict.get('entry_date'))
                    )
                    
                    if not patient_id or not enrollment_date:
                        logger.warning(f"跳过无效记录: 缺少必要字段")
                        continue
                    
                    record = PatientRecord(
                        patient_id=str(patient_id),
                        enrollment_date=enrollment_date,
                        raw_data=row_dict
                    )
                    records.append(record)
                
                except Exception as e:
                    logger.warning(f"处理记录时出错: {e}")
                    continue
            
            logger.info(f"从 {table_name} 表加载了 {len(records)} 条患者记录")
            return records
        
        except sqlite3.Error as e:
            logger.error(f"查询数据库失败: {e}")
            raise
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("SQLite数据库连接已关闭")


class CSVDataSource(DataSource):
    """CSV数据源"""
    
    def __init__(self, file_path: str):
        """
        初始化CSV数据源
        
        Args:
            file_path: CSV文件路径
        """
        self.file_path = file_path
    
    def load_data(self) -> List[PatientRecord]:
        """
        从CSV文件加载患者数据
        
        Returns:
            患者记录列表
        """
        try:
            # 读取CSV文件
            df = pd.read_csv(self.file_path)
            
            logger.info(f"从CSV文件加载了 {len(df)} 条记录: {self.file_path}")
            
            # 转换为PatientRecord
            records: List[PatientRecord] = []
            for _, row in df.iterrows():
                try:
                    row_dict = row.to_dict()
                    
                    # 处理NaN值
                    row_dict = {
                        k: (None if pd.isna(v) else v)
                        for k, v in row_dict.items()
                    }
                    
                    patient_id = row_dict.get('patient_id', row_dict.get('id', ''))
                    enrollment_date = row_dict.get(
                        'enrollment_date',
                        row_dict.get('enrollmentDate', row_dict.get('entry_date'))
                    )
                    
                    if not patient_id or not enrollment_date:
                        logger.warning(f"跳过无效记录: 缺少必要字段")
                        continue
                    
                    record = PatientRecord(
                        patient_id=str(patient_id),
                        enrollment_date=enrollment_date,
                        raw_data=row_dict
                    )
                    records.append(record)
                
                except Exception as e:
                    logger.warning(f"处理记录时出错: {e}")
                    continue
            
            logger.info(f"成功转换 {len(records)} 条患者记录")
            return records
        
        except Exception as e:
            logger.error(f"读取CSV文件失败: {e}")
            raise
    
    def close(self) -> None:
        """CSV数据源无需关闭"""
        pass


class ExcelDataSource(DataSource):
    """Excel数据源"""
    
    def __init__(self, file_path: str, sheet_name: str = 0):
        """
        初始化Excel数据源
        
        Args:
            file_path: Excel文件路径
            sheet_name: 工作表名称或索引
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
    
    def load_data(self) -> List[PatientRecord]:
        """
        从Excel文件加载患者数据
        
        Returns:
            患者记录列表
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
            
            logger.info(
                f"从Excel文件加载了 {len(df)} 条记录: {self.file_path} "
                f"(工作表: {self.sheet_name})"
            )
            
            # 转换为PatientRecord
            records: List[PatientRecord] = []
            for _, row in df.iterrows():
                try:
                    row_dict = row.to_dict()
                    
                    # 处理NaN值
                    row_dict = {
                        k: (None if pd.isna(v) else v)
                        for k, v in row_dict.items()
                    }
                    
                    patient_id = row_dict.get('patient_id', row_dict.get('id', ''))
                    enrollment_date = row_dict.get(
                        'enrollment_date',
                        row_dict.get('enrollmentDate', row_dict.get('entry_date'))
                    )
                    
                    if not patient_id or not enrollment_date:
                        logger.warning(f"跳过无效记录: 缺少必要字段")
                        continue
                    
                    record = PatientRecord(
                        patient_id=str(patient_id),
                        enrollment_date=enrollment_date,
                        raw_data=row_dict
                    )
                    records.append(record)
                
                except Exception as e:
                    logger.warning(f"处理记录时出错: {e}")
                    continue
            
            logger.info(f"成功转换 {len(records)} 条患者记录")
            return records
        
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            raise
    
    def close(self) -> None:
        """Excel数据源无需关闭"""
        pass


class DataImporter:
    """数据导入器 - 管理数据源的创建和使用"""
    
    @staticmethod
    def create_source(
        source_type: str,
        connection_string: str,
        **kwargs
    ) -> DataSource:
        """
        创建数据源
        
        Args:
            source_type: 数据源类型 ('sqlite', 'csv', 'excel')
            connection_string: 连接字符串或文件路径
            **kwargs: 额外参数
            
        Returns:
            数据源对象
        """
        source_type = source_type.lower()
        
        if source_type == 'sqlite':
            return SQLiteDataSource(connection_string)
        elif source_type == 'csv':
            return CSVDataSource(connection_string)
        elif source_type == 'excel':
            sheet_name = kwargs.get('sheet_name', 0)
            return ExcelDataSource(connection_string, sheet_name)
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")
    
    @staticmethod
    def import_from_config(config: Config) -> List[PatientRecord]:
        """
        使用配置文件导入数据
        
        Args:
            config: 配置对象
            
        Returns:
            患者记录列表
        """
        source_type = config.get('data_source.type', 'sqlite')
        connection_string = config.get('data_source.connection_string')
        
        if not connection_string:
            raise ValueError("未在配置中指定数据源连接字符串")
        
        logger.info(f"从 {source_type} 数据源导入数据: {connection_string}")
        
        source = DataImporter.create_source(source_type, connection_string)
        
        try:
            return source.load_data()
        finally:
            source.close()
