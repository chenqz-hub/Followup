"""
测试 - 数据导入
"""

import pytest
import os
import tempfile
import pandas as pd
from pathlib import Path
from src.data_importer import DataImporter, CSVDataSource, ExcelDataSource


class TestCSVDataSource:
    """CSV数据源测试"""
    
    @pytest.fixture
    def sample_csv(self):
        """创建示例CSV文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("patient_id,enrollment_date,age,death_date\n")
            f.write("P001,2020-01-01,55,2021-06-15\n")
            f.write("P002,2020-01-15,60,\n")
            f.write("P003,2020-02-01,65,2021-12-31\n")
            return f.name
    
    def test_load_csv_data(self, sample_csv):
        """测试从CSV加载数据"""
        source = CSVDataSource(sample_csv)
        records = source.load_data()
        
        assert len(records) == 3
        assert records[0].patient_id == 'P001'
        
        # 清理
        os.unlink(sample_csv)
    
    def test_csv_with_missing_fields(self):
        """测试包含缺失必需字段的CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            f.write("patient_id,enrollment_date\n")
            f.write("P001,2020-01-01\n")
            f.write(",2020-01-15\n")  # 缺少patient_id
            filename = f.name
        
        source = CSVDataSource(filename)
        records = source.load_data()
        
        # 应该只加载有效的记录
        assert len(records) == 1
        assert records[0].patient_id == 'P001'
        
        os.unlink(filename)


class TestDataImporter:
    """数据导入器测试"""
    
    def test_create_csv_source(self):
        """测试创建CSV数据源"""
        source = DataImporter.create_source('csv', 'test.csv')
        assert isinstance(source, CSVDataSource)
    
    def test_create_excel_source(self):
        """测试创建Excel数据源"""
        source = DataImporter.create_source('excel', 'test.xlsx')
        assert isinstance(source, ExcelDataSource)
    
    def test_create_unsupported_source(self):
        """测试不支持的数据源类型"""
        with pytest.raises(ValueError):
            DataImporter.create_source('unsupported_type', 'test.file')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
