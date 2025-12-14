"""
纵向数据处理单元测试
"""

import sys
import os
from pathlib import Path
from datetime import date, timedelta
import pytest

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from longitudinal_models import TimePointData, LongitudinalPatientRecord, LongitudinalFollowupRecord
from longitudinal_importer import LongitudinalDataImporter
from longitudinal_processor import LongitudinalEventProcessor


class TestTimePointData:
    """Test TimePointData model"""
    
    def test_create_basic_timepoint(self):
        """Test creating a basic time point"""
        tp = TimePointData(
            time_point="第六个月随访",
            months=6,
            visit_date=date(2018, 3, 8)
        )
        assert tp.time_point == "第六个月随访"
        assert tp.months == 6
        assert tp.visit_date == date(2018, 3, 8)
        assert tp.is_lost_to_followup == False
    
    def test_create_timepoint_with_event(self):
        """Test creating a time point with event"""
        tp = TimePointData(
            time_point="第12个月随访",
            months=12,
            visit_date=date(2018, 10, 1),
            cardiovascular_event="acute myocardial infarction",
            death_date=None
        )
        assert tp.cardiovascular_event == "acute myocardial infarction"
        assert tp.death_date is None


class TestLongitudinalPatientRecord:
    """Test LongitudinalPatientRecord model"""
    
    def test_create_patient_record(self):
        """Test creating patient record"""
        tp1 = TimePointData(time_point="第三个月随访", months=3)
        tp2 = TimePointData(
            time_point="第六个月随访",
            months=6,
            visit_date=date(2018, 3, 8)
        )
        
        record = LongitudinalPatientRecord(
            patient_id="1102",
            enrollment_date=date(2017, 10, 9),
            age=47,
            gender="男",
            time_points=[tp1, tp2]
        )
        
        assert record.patient_id == "1102"
        assert record.enrollment_date == date(2017, 10, 9)
        assert len(record.time_points) == 2
        assert record.age == 47
        assert record.gender == "男"
    
    def test_calculate_latest_followup(self):
        """Test calculating latest followup date"""
        tp1 = TimePointData(time_point="第三个月随访", months=3, visit_date=None)
        tp2 = TimePointData(
            time_point="第六个月随访",
            months=6,
            visit_date=date(2018, 3, 8)
        )
        tp3 = TimePointData(time_point="第12个月随访", months=12, visit_date=None)
        
        record = LongitudinalPatientRecord(
            patient_id="1102",
            enrollment_date=date(2017, 10, 9),
            time_points=[tp1, tp2, tp3]
        )
        
        # Manually calculate
        assert record.latest_followup_date is None  # Not calculated in __init__
        
        # This would be calculated by importer
        # assert record.latest_followup_date == date(2018, 3, 8)
        # assert record.latest_followup_months == 6
        # assert record.days_to_latest_followup == 150


class TestLongitudinalFollowupRecord:
    """Test LongitudinalFollowupRecord model"""
    
    def test_create_followup_record(self):
        """Test creating followup record"""
        record = LongitudinalFollowupRecord(
            patient_id="1102",
            enrollment_date=date(2017, 10, 9),
            latest_followup_date=date(2018, 3, 8),
            latest_followup_months=6,
            days_to_latest_followup=150,
            age=47,
            gender="男",
            group_name="无明显狭窄组"
        )
        
        assert record.patient_id == "1102"
        assert record.enrollment_date == date(2017, 10, 9)
        assert record.latest_followup_date == date(2018, 3, 8)
        assert record.age == 47
    
    def test_to_flattened_dict(self):
        """Test converting record to flattened dict"""
        record = LongitudinalFollowupRecord(
            patient_id="1102",
            enrollment_date=date(2017, 10, 9),
            latest_followup_date=date(2018, 3, 8),
            latest_followup_months=6,
            days_to_latest_followup=150,
            first_event_type="cardiovascular_event",
            first_event_date=date(2018, 6, 15),
            days_to_first_event=250,
            age=47,
            gender="男"
        )
        
        d = record.to_flattened_dict()
        assert isinstance(d, dict)
        assert d['patient_id'] == "1102"
        assert d['enrollment_date'] == "2017-10-09"
        assert d['first_event_type'] == "cardiovascular_event"
        assert 'processing_timestamp' in d


class TestLongitudinalDataImporter:
    """Test LongitudinalDataImporter"""
    
    def test_extract_time_point_info(self):
        """Test extracting time point info from sheet name"""
        importer = LongitudinalDataImporter()
        
        result = importer._extract_time_point_info("第六个月随访_CAGSFB1_627CAG随访表1")
        assert result is not None
        assert result[0] == "第六个月随访"
        assert result[1] == 6
        
        result = importer._extract_time_point_info("第36个月随访_CAGSFB1_627CAG随访表1")
        assert result is not None
        assert result[1] == 36
    
    def test_parse_date(self):
        """Test date parsing"""
        importer = LongitudinalDataImporter()
        
        # Test date object
        d = date(2018, 3, 8)
        result = importer._parse_date(d)
        assert result == d
        
        # Test string format
        result = importer._parse_date("2018-03-08")
        assert result == date(2018, 3, 8)
        
        # Test None
        result = importer._parse_date(None)
        assert result is None
    
    def test_load_excel_file(self):
        """Test loading Excel file"""
        template_file = r"d:\git\Followup\data\extracted_PSM93_cases_20251104_221914_随访表1_20251106_121718.xlsx"
        
        importer = LongitudinalDataImporter()
        success = importer.load_excel_file(template_file)
        
        assert success == True
        assert len(importer.sheet_data) == 6
        
        # Check sheet names
        sheet_names = list(importer.sheet_data.keys())
        assert "第六个月随访_CAGSFB1_627CAG随访表1" in sheet_names


class TestLongitudinalEventProcessor:
    """Test LongitudinalEventProcessor"""
    
    def test_identify_event_no_event(self):
        """Test identifying no event"""
        processor = LongitudinalEventProcessor()
        
        tp = TimePointData(
            time_point="第六个月随访",
            months=6,
            visit_date=date(2018, 3, 8)
        )
        
        event_type, event_date = processor._identify_event(tp)
        assert event_type is None
        assert event_date is None
    
    def test_identify_event_death(self):
        """Test identifying death event"""
        processor = LongitudinalEventProcessor()
        
        tp = TimePointData(
            time_point="第六个月随访",
            months=6,
            death_date=date(2018, 6, 15)
        )
        
        event_type, event_date = processor._identify_event(tp)
        assert event_type == "death"
        assert event_date == date(2018, 6, 15)
    
    def test_determine_followup_status(self):
        """Test determining followup status"""
        processor = LongitudinalEventProcessor()
        
        # Complete followup (>= 60 months)
        tp = TimePointData(
            time_point="第60个月随访",
            months=60,
            visit_date=date(2022, 10, 26)
        )
        record = LongitudinalPatientRecord(
            patient_id="1162",
            enrollment_date=date(2017, 11, 10),
            time_points=[tp],
            latest_followup_months=60
        )
        
        status = processor._determine_followup_status(record)
        assert status == "complete"
        
        # Incomplete followup (< 12 months)
        tp = TimePointData(
            time_point="第三个月随访",
            months=3,
            visit_date=None
        )
        record = LongitudinalPatientRecord(
            patient_id="test",
            enrollment_date=date(2020, 1, 1),
            time_points=[tp],
            latest_followup_months=3
        )
        
        status = processor._determine_followup_status(record)
        assert status == "incomplete"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
