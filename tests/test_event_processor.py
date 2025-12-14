"""
测试 - 事件处理器
"""

import pytest
from datetime import date, datetime, timedelta
from src.config import Config
from src.data_models import PatientRecord, EventInfo, FollowupRecord
from src.event_processor import EventProcessor


class TestEventProcessor:
    """事件处理器测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        config = Config('config/config.yaml')
        return config
    
    @pytest.fixture
    def processor(self, config):
        """创建事件处理器"""
        return EventProcessor(config)
    
    @pytest.fixture
    def sample_patient(self):
        """创建样例患者记录"""
        enrollment_date = date(2020, 1, 1)
        return PatientRecord(
            patient_id="P001",
            enrollment_date=enrollment_date,
            raw_data={
                'patient_id': 'P001',
                'enrollment_date': enrollment_date,
                'death_date': date(2021, 6, 15),
                'mi_date': date(2021, 3, 10),
                'stroke_date': date(2021, 9, 20),
            }
        )
    
    def test_date_parsing_with_date_object(self, processor):
        """测试日期对象的解析"""
        result = processor._parse_date(date(2021, 1, 1), 'test', 'test_field')
        assert result == date(2021, 1, 1)
    
    def test_date_parsing_with_string(self, processor):
        """测试字符串日期的解析"""
        test_cases = [
            ('2021-01-15', date(2021, 1, 15)),
            ('2021/01/15', date(2021, 1, 15)),
            ('15-01-2021', date(2021, 1, 15)),
            ('20210115', date(2021, 1, 15)),
        ]
        
        for date_str, expected in test_cases:
            result = processor._parse_date(date_str, 'test', 'test_field')
            assert result == expected, f"Failed for {date_str}"
    
    def test_date_parsing_with_datetime(self, processor):
        """测试datetime对象的解析"""
        dt = datetime(2021, 1, 15, 10, 30, 0)
        result = processor._parse_date(dt, 'test', 'test_field')
        assert result == date(2021, 1, 15)
    
    def test_days_difference_calculation(self, processor):
        """测试天数差异计算"""
        enrollment = date(2020, 1, 1)
        event = date(2020, 1, 11)
        
        days = processor._calculate_days_diff(enrollment, event)
        assert days == 10
    
    def test_days_difference_with_negative_days(self, processor):
        """测试早于入组时间的事件"""
        enrollment = date(2020, 1, 11)
        event = date(2020, 1, 1)
        
        days = processor._calculate_days_diff(enrollment, event, validate=True)
        assert days is None
    
    def test_extract_events_from_record(self, processor, sample_patient):
        """测试从患者记录中提取事件"""
        events = processor.extract_events_from_record(sample_patient)
        
        assert len(events) == 3
        assert events[0].event_type == 'myocardial_infarction'  # 最早的事件
        assert events[0].days_from_enrollment == 69
    
    def test_find_first_event(self, processor, sample_patient):
        """测试找出首次事件"""
        events = processor.extract_events_from_record(sample_patient)
        first_event, total = processor.find_first_event(events)
        
        assert first_event is not None
        assert first_event.event_type == 'myocardial_infarction'
        assert total == 3
    
    def test_find_first_event_with_no_events(self, processor):
        """测试没有事件时的处理"""
        first_event, total = processor.find_first_event([])
        
        assert first_event is None
        assert total == 0
    
    def test_process_patient(self, processor, sample_patient):
        """测试完整的患者处理流程"""
        followup = processor.process_patient(sample_patient)
        
        assert followup.patient_id == "P001"
        assert followup.first_event_type == 'myocardial_infarction'
        assert followup.days_to_first_event == 69
        assert followup.event_count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
