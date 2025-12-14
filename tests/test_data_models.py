"""
测试 - 数据模型
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from src.data_models import PatientRecord, EventInfo, FollowupRecord


class TestEventInfo:
    """事件信息模型测试"""
    
    def test_create_event_info(self):
        """测试创建事件信息"""
        event = EventInfo(
            event_type='death',
            event_date=date(2021, 1, 15),
            days_from_enrollment=100,
            data_source='death_date'
        )
        
        assert event.event_type == 'death'
        assert event.event_date == date(2021, 1, 15)
        assert event.days_from_enrollment == 100
    
    def test_event_info_with_negative_days(self):
        """测试负数天数会失败"""
        with pytest.raises(ValidationError):
            EventInfo(
                event_type='death',
                event_date=date(2021, 1, 15),
                days_from_enrollment=-10,
                data_source='death_date'
            )


class TestPatientRecord:
    """患者记录模型测试"""
    
    def test_create_patient_record(self):
        """测试创建患者记录"""
        patient = PatientRecord(
            patient_id='P001',
            enrollment_date=date(2020, 1, 1),
            age=55,
            gender='M'
        )
        
        assert patient.patient_id == 'P001'
        assert patient.enrollment_date == date(2020, 1, 1)
        assert patient.age == 55
    
    def test_patient_record_with_future_date(self):
        """测试未来日期会失败"""
        future_date = date(2099, 12, 31)
        with pytest.raises(ValidationError):
            PatientRecord(
                patient_id='P001',
                enrollment_date=future_date
            )
    
    def test_patient_record_with_raw_data(self):
        """测试包含原始数据的患者记录"""
        raw_data = {
            'patient_id': 'P001',
            'enrollment_date': date(2020, 1, 1),
            'death_date': date(2021, 6, 15),
            'age': 55
        }
        
        patient = PatientRecord(
            patient_id='P001',
            enrollment_date=date(2020, 1, 1),
            raw_data=raw_data
        )
        
        assert patient.raw_data == raw_data


class TestFollowupRecord:
    """随访记录模型测试"""
    
    def test_create_followup_record(self):
        """测试创建随访记录"""
        followup = FollowupRecord(
            patient_id='P001',
            enrollment_date=date(2020, 1, 1),
            first_event_type='death',
            first_event_date=date(2021, 1, 15),
            days_to_first_event=380,
            event_count=1
        )
        
        assert followup.patient_id == 'P001'
        assert followup.first_event_type == 'death'
        assert followup.days_to_first_event == 380
    
    def test_followup_record_with_negative_days(self):
        """测试负数天数会失败"""
        with pytest.raises(ValidationError):
            FollowupRecord(
                patient_id='P001',
                enrollment_date=date(2020, 1, 1),
                first_event_type='death',
                first_event_date=date(2021, 1, 15),
                days_to_first_event=-10,
                event_count=1
            )
    
    def test_followup_record_to_flattened_dict(self):
        """测试转换为展平字典"""
        event = EventInfo(
            event_type='death',
            event_date=date(2021, 1, 15),
            days_from_enrollment=380
        )
        
        followup = FollowupRecord(
            patient_id='P001',
            enrollment_date=date(2020, 1, 1),
            first_event_type='death',
            first_event_date=date(2021, 1, 15),
            days_to_first_event=380,
            event_count=1,
            all_events=[event]
        )
        
        flattened = followup.to_flattened_dict()
        
        assert flattened['patient_id'] == 'P001'
        assert flattened['first_event_type'] == 'death'
        assert flattened['days_to_first_event'] == 380
        assert 'enrollment_date' in flattened


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
