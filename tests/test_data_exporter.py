"""
测试 - 数据导出
"""

import pytest
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
import pandas as pd
from src.data_models import FollowupRecord, EventInfo
from src.data_exporter import CSVExporter, ExcelExporter, FollowupExporter
from src.config import Config


class TestCSVExporter:
    """CSV导出器测试"""
    
    @pytest.fixture
    def sample_records(self):
        """创建示例随访记录"""
        event = EventInfo(
            event_type='death',
            event_date=date(2021, 1, 15),
            days_from_enrollment=380
        )
        
        return [
            FollowupRecord(
                patient_id='P001',
                enrollment_date=date(2020, 1, 1),
                first_event_type='death',
                first_event_date=date(2021, 1, 15),
                days_to_first_event=380,
                event_count=1,
                all_events=[event]
            ),
            FollowupRecord(
                patient_id='P002',
                enrollment_date=date(2020, 1, 1),
                first_event_type=None,
                first_event_date=None,
                days_to_first_event=None,
                event_count=0,
                all_events=[]
            )
        ]
    
    def test_export_to_csv(self, sample_records):
        """测试CSV导出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_output.csv')
            
            exporter = CSVExporter()
            result = exporter.export(sample_records, output_file)
            
            assert os.path.exists(result)
            
            # 验证导出的内容
            df = pd.read_csv(result)
            assert len(df) == 2
            assert 'patient_id' in df.columns
            assert df.iloc[0]['patient_id'] == 'P001'


class TestExcelExporter:
    """Excel导出器测试"""
    
    @pytest.fixture
    def sample_records(self):
        """创建示例随访记录"""
        event = EventInfo(
            event_type='death',
            event_date=date(2021, 1, 15),
            days_from_enrollment=380
        )
        
        return [
            FollowupRecord(
                patient_id='P001',
                enrollment_date=date(2020, 1, 1),
                first_event_type='death',
                first_event_date=date(2021, 1, 15),
                days_to_first_event=380,
                event_count=1,
                all_events=[event]
            )
        ]
    
    def test_export_to_excel(self, sample_records):
        """测试Excel导出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'test_output.xlsx')
            
            exporter = ExcelExporter()
            result = exporter.export(sample_records, output_file)
            
            assert os.path.exists(result)
            
            # 验证导出的内容
            df = pd.read_excel(result, sheet_name='Follow-up Data')
            assert len(df) == 1
            assert 'patient_id' in df.columns


class TestFollowupExporter:
    """随访导出管理器测试"""
    
    def test_exporter_initialization(self):
        """测试导出管理器初始化"""
        config = Config('config/config.yaml')
        exporter = FollowupExporter(config)
        
        assert exporter.output_dir == config.get('output.output_dir', 'output')
        assert exporter.output_format == config.get('output.format', 'excel')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
