"""事件处理器测试"""

import pytest
from datetime import date
import tempfile
import yaml
from pathlib import Path
from src.event_processor import EventProcessor
from src.config import Config
from src.data_models import PatientRecord, EventInfo


class TestEventProcessor:
    """EventProcessor测试"""

    @pytest.fixture
    def processor(self, sample_config_dict):
        """创建事件处理器"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(sample_config_dict, f)
            temp_path = f.name

        config = Config(temp_path)
        Path(temp_path).unlink()
        return EventProcessor(config)

    def test_calculate_days_between_dates(self, processor):
        """测试日期间隔计算"""
        start = date(2020, 1, 1)
        end = date(2020, 1, 31)
        days = processor._calculate_days_diff(start, end)
        assert days == 30

    def test_identify_events_from_patient(self, processor):
        """测试从患者数据识别事件"""
        patient = PatientRecord(
            patient_id="P001",
            enrollment_date=date(2020, 1, 1),
            raw_data={"death_date": date(2021, 6, 15)},
        )
        events = processor.extract_events_from_record(patient)

        assert len(events) > 0
        # 应该识别到死亡事件
        death_events = [e for e in events if e.event_type == "death"]
        assert len(death_events) == 1
        assert death_events[0].event_date == date(2021, 6, 15)

    def test_select_first_event(self, processor):
        """测试选择首次事件"""
        events = [
            EventInfo(event_type="mi", event_date=date(2021, 3, 1), days_from_enrollment=425),
            EventInfo(event_type="death", event_date=date(2021, 6, 15), days_from_enrollment=530),
        ]
        first_event, count = processor.find_first_event(events)
        # 应该选择最早发生的事件
        assert first_event.event_type == "mi"
        assert first_event.days_from_enrollment == 425
        assert count == 2

    def test_process_patient_with_event(self, processor):
        """测试处理有事件的患者"""
        patient = PatientRecord(
            patient_id="P001",
            enrollment_date=date(2020, 1, 1),
            raw_data={"death_date": date(2021, 6, 15)},
        )
        followup = processor.process_patient(patient)

        assert followup.patient_id == "P001"
        assert followup.first_event_type == "death"
        assert followup.days_to_first_event == 531  # 2021-06-15 - 2020-01-01

    def test_process_patient_without_event(self, processor):
        """测试处理无事件的患者"""
        patient = PatientRecord(patient_id="P003", enrollment_date=date(2020, 1, 1))
        followup = processor.process_patient(patient)

        assert followup.patient_id == "P003"
        assert followup.first_event_type is None
        assert followup.days_to_first_event is None
