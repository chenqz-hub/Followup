"""
纵向数据导入模块 - 支持从多个Sheet导入并合并纵向数据
"""

import logging
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import date, datetime, timedelta
import re

from longitudinal_models import LongitudinalPatientRecord, TimePointData
from logger import setup_logger

logger = logging.getLogger(__name__)


class LongitudinalDataImporter:
    """纵向数据导入器 - 从多Sheet Excel文件导入纵向随访数据"""
    
    # 事件类型编码映射 (基于编码本)
    EVENT_TYPE_CODES = {
        '1': 'death',  # 心源性死亡
        '2': 'mi',  # 非致死性心肌梗死
        '3': 'revascularization',  # 靶病变血运重建
        '4': 'heart_failure',  # 心衰发作
        '5': 'angina',  # 心绞痛
        '6': 'hospitalization',  # 因心脏病入院
    }
    
    # 时间点名称到月数的映射（用于自动识别）
    TIME_POINT_PATTERNS = [
        (r'第?一个?月|1个?月', 1),
        (r'第?三个?月|3个?月', 3),
        (r'第?六个?月|6个?月', 6),
        (r'第?12个?月', 12),
        (r'第?18个?月', 18),
        (r'第?24个?月', 24),
        (r'第?30个?月', 30),
        (r'第?36个?月', 36),
        (r'第?42个?月', 42),
        (r'第?48个?月', 48),
        (r'第?54个?月', 54),
        (r'第?60个?月', 60),
        (r'第?66个?月', 66),
        (r'第?72个?月', 72),
        (r'第?84个?月', 84),
        (r'第?90个?月', 90),
        (r'第?96个?月', 96),
        (r'第?108个?月', 108),
        (r'第?120个?月', 120),
    ]
    
    # 关键字段映射
    FIELD_MAPPING = {
        'patient_id': ['subjid', 'patient_id'],
        'patient_name': ['stname', 'patient_name', '姓名'],
        'birthday': ['sys_dateofbirth', 'dateofbirth', 'birthday', 'birth_date', '出生日期'],
        'enrollment_date': ['groupdate', 'enrollment_date'],
        'visit_date': ['随访日期1', 'visit_date'],
        'death_date': ['死亡时间1', 'death_date'],
        'death_reason': ['死亡原因1', 'death_reason'],
        'loss_to_followup': ['随访缺失1', 'loss_to_followup'],
        'loss_reason': ['失访原因1', 'loss_reason'],
        'cardiovascular_event': ['随访期间心血管不良事件1', '随访期间主要心血管不良事件1', 'cardiovascular_event'],
        'event_type': ['如有不良事件，何事件1', '心血管事件1', 'event_type'],
        'coronary_intervention': ['冠脉造影,冠脉CT或介入治疗1', 'coronary_intervention'],
        'intervention_date': ['冠脉造影,冠脉CT或介入治疗时间1', 'intervention_date'],
        'coronary_bypass': ['后续冠脉搭桥1', 'coronary_bypass'],
        'bypass_date': ['冠脉搭桥日期1', 'bypass_date'],
        'revascularization_treatment': ['自最近一次联系后进行血运重建治疗1', 'revascularization_treatment'],
        'revascularization_type': ['如是，何治疗1', 'revascularization_type'],
        'revascularization_date': ['治疗时间1', 'revascularization_date'],
        'revascularization_detail': ['治疗详细说明', 'revascularization_detail'],
        'symptoms': ['随访1 目前症状', 'symptoms'],
        'diagnosis': ['随访1 目前诊断', 'diagnosis'],
    }
    
    def __init__(self):
        """初始化导入器"""
        self.excel_file: Optional[str] = None
        self.sheet_data: Dict[str, pd.DataFrame] = {}
    
    def load_excel_file(self, file_path: str) -> bool:
        """
        加载Excel文件并读取所有Sheet
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            是否成功加载
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            xls = pd.ExcelFile(file_path)
            self.excel_file = file_path
            
            logger.info(f"加载Excel文件: {file_path}")
            logger.info(f"发现{len(xls.sheet_names)}个Sheet")
            
            # 加载所有Sheet
            for sheet_name in xls.sheet_names:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self.sheet_data[sheet_name] = df
                    logger.debug(f"  加载Sheet: {sheet_name} ({len(df)}行)")
                except Exception as e:
                    logger.warning(f"  加载Sheet失败: {sheet_name} - {e}")
                    continue
            
            return len(self.sheet_data) > 0
        
        except Exception as e:
            logger.error(f"加载Excel文件失败: {e}")
            return False
    
    def _get_field_value(self, row: pd.Series, field_mapping_keys: List[str]) -> Optional:
        """
        从行数据中获取字段值（支持多个可能的列名）
        
        Args:
            row: DataFrame行
            field_mapping_keys: 可能的字段名列表
            
        Returns:
            字段值，或None
        """
        for key in field_mapping_keys:
            if key in row.index:
                value = row[key]
                # 处理NaN
                if pd.isna(value):
                    continue
                # 处理空字符串
                if isinstance(value, str) and value.strip() == '':
                    continue
                return value
        return None
    
    def _parse_event_codes(self, event_code_value: any) -> List[str]:
        """
        解析事件编码，将编码转换为事件类型列表
        
        Args:
            event_code_value: 事件编码值（可能是单个数字、逗号分隔的数字，或其他格式）
            
        Returns:
            事件类型列表（例如 ['angina', 'hospitalization']）
        """
        if event_code_value is None or pd.isna(event_code_value):
            return []
        
        # 转换为字符串
        code_str = str(event_code_value).strip()
        
        if not code_str or code_str == '':
            return []
        
        # 分割逗号分隔的编码
        codes = [c.strip() for c in code_str.split(',')]
        
        # 映射编码到事件类型
        event_types = []
        for code in codes:
            if code in self.EVENT_TYPE_CODES:
                event_types.append(self.EVENT_TYPE_CODES[code])
            else:
                # 未知编码，记录警告
                logger.debug(f"未识别的事件编码: {code}")
        
        return event_types
    
    def _parse_date(self, value) -> Optional[date]:
        """
        解析日期值
        
        Args:
            value: 日期值（可能是多种格式）
            
        Returns:
            解析后的date对象，或None
        """
        if value is None or pd.isna(value):
            return None
        
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            
            # 尝试多种日期格式
            date_formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%d-%m-%Y',
                '%d/%m/%Y',
                '%Y%m%d',
                '%m/%d/%Y',
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            logger.debug(f"无法解析日期: {value}")
            return None
        
        # 尝试Excel日期码
        try:
            if isinstance(value, (int, float)):
                return date(1900, 1, 1) + timedelta(days=int(value) - 2)
        except (ValueError, OverflowError):
            pass
        
        return None
    
    def _extract_time_point_info(self, sheet_name: str) -> Optional[Tuple[str, int]]:
        """
        从sheet名称中提取时间点信息（使用正则匹配）
        
        Args:
            sheet_name: Sheet名称
            
        Returns:
            (时间点名称, 月数) 或 None
        """
        for pattern, months in self.TIME_POINT_PATTERNS:
            if re.search(pattern, sheet_name):
                return (sheet_name, months)  # 返回完整sheet名称作为时间点名称
        
        # 尝试直接从数字提取月数（例如 "6M" "12个月" 等）
        match = re.search(r'(\d+)\s*[Mm个月]', sheet_name)
        if match:
            months = int(match.group(1))
            return (sheet_name, months)
        
        logger.warning(f"无法从sheet名称提取时间点信息: {sheet_name}")
        return None
    
    def import_longitudinal_data(self) -> List[LongitudinalPatientRecord]:
        """
        导入纵向数据并合并为LongitudinalPatientRecord列表
        
        Returns:
            纵向患者记录列表
        """
        if not self.sheet_data:
            logger.error("未加载任何Sheet数据")
            return []
        
        # 首先获取患者列表（从第一个Sheet）
        first_sheet = list(self.sheet_data.values())[0]
        patient_ids = self._get_unique_patients(first_sheet)
        
        logger.info(f"发现{len(patient_ids)}个患者")
        
        # 为每个患者创建纵向记录
        longitudinal_records: List[LongitudinalPatientRecord] = []
        
        for patient_id in patient_ids:
            try:
                record = self._create_longitudinal_record(patient_id)
                if record:
                    longitudinal_records.append(record)
            except Exception as e:
                logger.warning(f"处理患者{patient_id}时出错: {e}")
                continue
        
        logger.info(f"成功创建{len(longitudinal_records)}条纵向患者记录")
        return longitudinal_records
    
    def _get_unique_patients(self, df: pd.DataFrame) -> List[str]:
        """获取患者ID列表"""
        patient_id_cols = ['subjid', 'patient_id']
        for col in patient_id_cols:
            if col in df.columns:
                return df[col].unique().tolist()
        return []
    
    def _get_basic_info_sheet(self) -> Optional[pd.DataFrame]:
        """
        查找并返回基本信息Sheet（通常命名为'***基本信息'）
        
        Returns:
            基本信息DataFrame或None
        """
        # 优先查找包含"基本信息"的sheet
        for sheet_name, df in self.sheet_data.items():
            if '基本信息' in sheet_name:
                logger.info(f"找到基本信息Sheet: {sheet_name}")
                return df
        
        # 如果没有找到，返回第一个sheet
        if self.sheet_data:
            first_sheet_name = list(self.sheet_data.keys())[0]
            logger.warning(f"未找到'基本信息'Sheet，使用第一个Sheet: {first_sheet_name}")
            return self.sheet_data[first_sheet_name]
        
        return None
    
    def _extract_basic_info(self, patient_id: str, basic_info_df: pd.DataFrame) -> Dict[str, any]:
        """
        从基本信息Sheet中提取患者基本信息
        
        Args:
            patient_id: 患者ID
            basic_info_df: 基本信息DataFrame
            
        Returns:
            包含基本信息的字典
        """
        basic_info = {
            'name': None,
            'birthday': None,
            'age': None,
            'gender': None,
            'enrollment_date': None,
            'group_name': None,
        }
        
        # 查找该患者在基本信息表中的行
        patient_rows = basic_info_df[basic_info_df['subjid'] == patient_id] if 'subjid' in basic_info_df.columns else None
        
        if patient_rows is None or len(patient_rows) == 0:
            logger.debug(f"患者{patient_id}在基本信息表中无数据")
            return basic_info
        
        row = patient_rows.iloc[0]
        
        # 提取姓名
        name_value = self._get_field_value(row, self.FIELD_MAPPING['patient_name'])
        if name_value is not None:
            basic_info['name'] = str(name_value)
        
        # 提取生日
        birthday_value = self._get_field_value(row, self.FIELD_MAPPING['birthday'])
        basic_info['birthday'] = self._parse_date(birthday_value)
        
        # 提取入组日期
        enroll_date = self._get_field_value(row, self.FIELD_MAPPING['enrollment_date'])
        basic_info['enrollment_date'] = self._parse_date(enroll_date)
        
        # 提取年龄
        if 'sys_currentage' in row.index and pd.notna(row['sys_currentage']):
            try:
                basic_info['age'] = int(row['sys_currentage'])
            except (ValueError, TypeError):
                pass
        
        # 提取性别
        if 'stsex' in row.index:
            gender_value = row['stsex']
            if pd.notna(gender_value):
                try:
                    gender_int = int(gender_value)
                    basic_info['gender'] = '男' if gender_int == 1 else '女'
                except (ValueError, TypeError):
                    basic_info['gender'] = str(gender_value)
        
        # 提取分组
        if 'groupname' in row.index:
            basic_info['group_name'] = row['groupname'] if pd.notna(row['groupname']) else None
        
        return basic_info
    
    def _create_longitudinal_record(self, patient_id: str) -> Optional[LongitudinalPatientRecord]:
        """
        为单个患者创建纵向记录
        
        Args:
            patient_id: 患者ID
            
        Returns:
            LongitudinalPatientRecord或None
        """
        time_points: List[TimePointData] = []
        
        # 首先从基本信息表中提取患者基本信息
        basic_info_df = self._get_basic_info_sheet()
        basic_info = self._extract_basic_info(patient_id, basic_info_df) if basic_info_df is not None else {}
        
        patient_name: Optional[str] = basic_info.get('name')
        patient_birthday: Optional[date] = basic_info.get('birthday')
        patient_enrollment_date: Optional[date] = basic_info.get('enrollment_date')
        patient_age: Optional[int] = basic_info.get('age')
        patient_gender: Optional[str] = basic_info.get('gender')
        patient_group: Optional[str] = basic_info.get('group_name')
        
        # 从每个Sheet中提取该患者的数据
        for sheet_name, df in self.sheet_data.items():
            # 提取时间点信息
            time_point_info = self._extract_time_point_info(sheet_name)
            if not time_point_info:
                logger.debug(f"无法识别Sheet的时间点: {sheet_name}")
                continue
            
            time_point_name, months = time_point_info
            
            # 找到该患者在该Sheet中的数据
            patient_rows = df[df['subjid'] == patient_id] if 'subjid' in df.columns else None
            
            if patient_rows is None or len(patient_rows) == 0:
                logger.debug(f"患者{patient_id}在Sheet{sheet_name}中无数据")
                continue
            
            row = patient_rows.iloc[0]
            
            # 如果基本信息表中没有入组日期，尝试从当前sheet获取（向后兼容）
            if patient_enrollment_date is None:
                enroll_date = self._get_field_value(row, self.FIELD_MAPPING['enrollment_date'])
                patient_enrollment_date = self._parse_date(enroll_date)
            
            # 提取时间点数据
            time_point_data = self._extract_time_point_data(row, time_point_name, months)
            time_points.append(time_point_data)
        
        if patient_enrollment_date is None:
            logger.warning(f"患者{patient_id}无入组日期，跳过")
            return None
        
        # 创建纵向患者记录
        record = LongitudinalPatientRecord(
            patient_id=str(patient_id),
            patient_name=patient_name,
            enrollment_date=patient_enrollment_date,
            birthday=patient_birthday,
            age=patient_age,
            gender=patient_gender,
            group_name=patient_group,
            time_points=time_points,
        )
        
        # 计算最晚随访时间
        self._calculate_latest_followup(record)
        
        return record
    
    def _extract_time_point_data(self, row: pd.Series, time_point_name: str, months: int) -> TimePointData:
        """
        从行数据中提取单个时间点的随访数据
        
        Args:
            row: DataFrame行
            time_point_name: 时间点名称
            months: 距入组的月数
            
        Returns:
            TimePointData对象
        """
        visit_date = self._parse_date(self._get_field_value(row, self.FIELD_MAPPING['visit_date']))
        death_date = self._parse_date(self._get_field_value(row, self.FIELD_MAPPING['death_date']))
        intervention_date = self._parse_date(self._get_field_value(row, self.FIELD_MAPPING['intervention_date']))
        bypass_date = self._parse_date(self._get_field_value(row, self.FIELD_MAPPING['bypass_date']))
        revascularization_date = self._parse_date(self._get_field_value(row, self.FIELD_MAPPING['revascularization_date']))
        
        loss_to_followup_value = self._get_field_value(row, self.FIELD_MAPPING['loss_to_followup'])
        is_lost = bool(loss_to_followup_value) if loss_to_followup_value is not None else False
        
        # 解析事件类型编码
        event_type_value = self._get_field_value(row, self.FIELD_MAPPING['event_type'])
        event_types = self._parse_event_codes(event_type_value)
        
        return TimePointData(
            time_point=time_point_name,
            months=months,
            visit_date=visit_date,
            is_lost_to_followup=is_lost,
            loss_reason=str(self._get_field_value(row, self.FIELD_MAPPING['loss_reason'])) if self._get_field_value(row, self.FIELD_MAPPING['loss_reason']) else None,
            death_date=death_date,
            death_reason=str(self._get_field_value(row, self.FIELD_MAPPING['death_reason'])) if self._get_field_value(row, self.FIELD_MAPPING['death_reason']) else None,
            cardiovascular_event=str(self._get_field_value(row, self.FIELD_MAPPING['cardiovascular_event'])) if self._get_field_value(row, self.FIELD_MAPPING['cardiovascular_event']) else None,
            event_types=event_types,  # 新增：解析后的事件类型列表
            coronary_intervention=str(self._get_field_value(row, self.FIELD_MAPPING['coronary_intervention'])) if self._get_field_value(row, self.FIELD_MAPPING['coronary_intervention']) else None,
            intervention_date=intervention_date,
            coronary_bypass=str(self._get_field_value(row, self.FIELD_MAPPING['coronary_bypass'])) if self._get_field_value(row, self.FIELD_MAPPING['coronary_bypass']) else None,
            bypass_date=bypass_date,
            revascularization_treatment=str(self._get_field_value(row, self.FIELD_MAPPING['revascularization_treatment'])) if self._get_field_value(row, self.FIELD_MAPPING['revascularization_treatment']) else None,
            revascularization_type=str(self._get_field_value(row, self.FIELD_MAPPING['revascularization_type'])) if self._get_field_value(row, self.FIELD_MAPPING['revascularization_type']) else None,
            revascularization_date=revascularization_date,
            revascularization_detail=str(self._get_field_value(row, self.FIELD_MAPPING['revascularization_detail'])) if self._get_field_value(row, self.FIELD_MAPPING['revascularization_detail']) else None,
            current_symptoms=str(self._get_field_value(row, self.FIELD_MAPPING['symptoms'])) if self._get_field_value(row, self.FIELD_MAPPING['symptoms']) else None,
            current_diagnosis=str(self._get_field_value(row, self.FIELD_MAPPING['diagnosis'])) if self._get_field_value(row, self.FIELD_MAPPING['diagnosis']) else None,
            raw_data=row.to_dict(),
        )
    
    def _calculate_latest_followup(self, record: LongitudinalPatientRecord) -> None:
        """
        计算患者的最晚随访时间
        
        Args:
            record: 纵向患者记录
        """
        if not record.time_points:
            return
        
        # 按时间点月数排序
        sorted_time_points = sorted(record.time_points, key=lambda tp: tp.months)
        
        # 从后往前找到首个有有效随访日期的时间点
        for time_point in reversed(sorted_time_points):
            if time_point.visit_date is not None:
                record.latest_followup_date = time_point.visit_date
                record.latest_followup_months = time_point.months
                
                # 计算天数差异
                if record.enrollment_date:
                    delta = time_point.visit_date - record.enrollment_date
                    record.days_to_latest_followup = delta.days
                
                logger.debug(
                    f"患者{record.patient_id}: 最晚随访时间点 = {time_point.time_point}, "
                    f"日期 = {time_point.visit_date}, "
                    f"天数差异 = {record.days_to_latest_followup}"
                )
                return
        
        # 如果没有随访日期，记录为None
        logger.debug(f"患者{record.patient_id}: 无有效随访日期")
