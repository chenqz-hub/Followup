"""数据模型测试"""

import pytest
from datetime import date
from src.data_models import PatientRecord, FollowupRecord, EventInfo


class TestPatientRecord:
    """PatientRecord测试"""

    def test_create_patient_record(self):
        """测试创建患者记录"""
        patient = PatientRecord(
            patient_id="P001",
            enrollment_date=date(2020, 1, 1),
            raw_data={"death_date": date(2021, 6, 15)},
        )
        assert patient.patient_id == "P001"
        assert patient.enrollment_date == date(2020, 1, 1)
        assert patient.raw_data["death_date"] == date(2021, 6, 15)

    def test_patient_with_dict(self):
        """测试使用字典创建患者记录"""
        data = {
            "patient_id": "P002",
            "enrollment_date": date(2020, 2, 1),
            "raw_data": {"mi_date": date(2021, 3, 15)},
        }
        patient = PatientRecord(**data)
        assert patient.patient_id == "P002"
        assert patient.raw_data["mi_date"] == date(2021, 3, 15)


class TestEventInfo:
    """EventInfo测试"""

    def test_create_event_info(self):
        """测试创建事件信息"""
        event = EventInfo(
            event_type="death", event_date=date(2021, 6, 15), days_from_enrollment=530
        )
        assert event.event_type == "death"
        assert event.days_from_enrollment == 530

    def test_event_with_data_source(self):
        """测试带数据源的事件"""
        event = EventInfo(
            event_type="death",
            event_date=date(2021, 6, 15),
            days_from_enrollment=530,
            data_source="death_date",
        )
        assert event.data_source == "death_date"


class TestFollowupRecord:
    """FollowupRecord测试"""

    def test_create_followup_record(self):
        """测试创建随访记录"""
        record = FollowupRecord(
            patient_id="P001",
            enrollment_date=date(2020, 1, 1),
            first_event_type="death",
            first_event_date=date(2021, 6, 15),
            days_to_first_event=530,
        )
        assert record.patient_id == "P001"
        assert record.first_event_type == "death"
        assert record.days_to_first_event == 530

    def test_followup_record_without_event(self):
        """测试没有事件的随访记录"""
        record = FollowupRecord(
            patient_id="P002",
            enrollment_date=date(2020, 1, 1),
            first_event_type=None,
            first_event_date=None,
            days_to_first_event=None,
        )
        assert record.first_event_type is None
        assert record.days_to_first_event is None
