"""
事件处理模块
负责事件识别、解析和处理
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from config import Config
from data_models import EventInfo, PatientRecord, FollowupRecord


logger = logging.getLogger(__name__)


class EventProcessor:
    """事件处理器 - 识别和处理患者事件"""
    
    def __init__(self, config: Config):
        """
        初始化事件处理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.event_types = config.get_nested('events').get('types', {})
        self.max_days = config.get('processing.max_days_from_enrollment', 36500)
        self.invalid_date_handling = config.get('processing.invalid_date_handling', 'skip')
    
    def extract_events_from_record(
        self,
        patient: PatientRecord,
    ) -> List[EventInfo]:
        """
        从患者记录中提取所有事件
        
        Args:
            patient: 患者记录对象
            
        Returns:
            事件列表，按时间排序
        """
        events: List[EventInfo] = []
        raw_data = patient.raw_data
        
        # 遍历所有事件类型
        for event_type, event_config in self.event_types.items():
            field_names = event_config.get('field_names', [])
            
            # 在原始数据中查找对应字段
            for field_name in field_names:
                if field_name not in raw_data:
                    continue
                
                field_value = raw_data.get(field_name)
                if field_value is None or str(field_value).strip() == '':
                    continue
                
                # 尝试解析日期
                parsed_date = self._parse_date(field_value, event_type, field_name)
                if parsed_date is None:
                    continue
                
                # 验证日期有效性
                days_diff = self._calculate_days_diff(patient.enrollment_date, parsed_date)
                if days_diff is None:
                    continue
                
                # 创建事件
                event = EventInfo(
                    event_type=event_type,
                    event_date=parsed_date,
                    days_from_enrollment=days_diff,
                    data_source=field_name
                )
                events.append(event)
                logger.debug(
                    f"患者 {patient.patient_id}: 检测到事件 {event_type} "
                    f"(字段: {field_name}, 日期: {parsed_date})"
                )
        
        # 按日期排序
        events.sort(key=lambda e: e.event_date)
        
        return events
    
    def _parse_date(
        self,
        value: Any,
        event_type: str,
        field_name: str
    ) -> Optional[date]:
        """
        解析日期值
        
        Args:
            value: 要解析的值
            event_type: 事件类型 (用于日志)
            field_name: 字段名 (用于日志)
            
        Returns:
            解析后的日期，或None如果无效
        """
        if value is None:
            return None
        
        # 如果已经是日期对象
        if isinstance(value, date):
            return value
        
        if isinstance(value, datetime):
            return value.date()
        
        # 尝试解析字符串
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
            
            # 无法解析
            if self.invalid_date_handling == 'skip':
                logger.warning(
                    f"无法解析日期值 '{value}' (事件类型: {event_type}, 字段: {field_name})"
                )
                return None
            elif self.invalid_date_handling == 'fill_with_null':
                return None
            elif self.invalid_date_handling == 'fill_with_today':
                return date.today()
        
        # 如果是数字，尝试作为Excel日期码
        try:
            if isinstance(value, (int, float)):
                # Excel日期码: 1是1900-01-01
                return date(1900, 1, 1) + timedelta(days=int(value) - 2)
        except (ValueError, OverflowError):
            pass
        
        logger.warning(
            f"无法识别日期格式 '{value}' (类型: {type(value).__name__}, "
            f"事件类型: {event_type}, 字段: {field_name})"
        )
        return None
    
    def _calculate_days_diff(
        self,
        enrollment_date: date,
        event_date: date,
        validate: bool = True
    ) -> Optional[int]:
        """
        计算事件发生距离入组时间的天数
        
        Args:
            enrollment_date: 入组日期
            event_date: 事件日期
            validate: 是否验证日期有效性
            
        Returns:
            天数差异，或None如果无效
        """
        try:
            days = (event_date - enrollment_date).days
            
            if validate:
                # 验证时间范围
                if days < 0:
                    logger.debug(
                        f"事件日期 {event_date} 早于入组日期 {enrollment_date}，已跳过"
                    )
                    return None
                
                if days > self.max_days:
                    logger.warning(
                        f"事件日期与入组日期相差过大 ({days} 天)，可能数据错误"
                    )
                    if self.config.get('processing.skip_invalid_records'):
                        return None
            
            return days
        
        except Exception as e:
            logger.error(f"计算天数差异时出错: {e}")
            return None
    
    def find_first_event(
        self,
        events: List[EventInfo],
        priority_order: Optional[Dict[str, int]] = None
    ) -> Tuple[Optional[EventInfo], int]:
        """
        从事件列表中找出首次事件
        
        按照事件优先级和时间顺序确定首次事件
        
        Args:
            events: 事件列表
            priority_order: 事件类型优先级 (数字越小优先级越高)
            
        Returns:
            (首次事件, 总事件数) 元组
        """
        if not events:
            return None, 0
        
        # 获取优先级配置
        if priority_order is None:
            priority_order = {
                event_type: config.get('priority', float('inf'))
                for event_type, config in self.event_types.items()
            }
        
        # 按时间排序
        events_sorted_by_time = sorted(events, key=lambda e: e.event_date)
        
        # 找出最早发生的事件
        first_event = events_sorted_by_time[0]
        
        # 查找同一天或之后的其他事件中优先级更高的
        earliest_date = first_event.event_date
        same_date_events = [e for e in events if e.event_date == earliest_date]
        
        if same_date_events:
            # 按优先级排序
            same_date_events.sort(
                key=lambda e: priority_order.get(e.event_type, float('inf'))
            )
            first_event = same_date_events[0]
        
        return first_event, len(events)
    
    def process_patient(
        self,
        patient: PatientRecord
    ) -> FollowupRecord:
        """
        处理患者，生成随访记录
        
        Args:
            patient: 患者记录
            
        Returns:
            随访记录
        """
        # 提取所有事件
        events = self.extract_events_from_record(patient)
        
        # 找出首次事件
        first_event, total_events = self.find_first_event(events)
        
        # 创建随访记录
        followup = FollowupRecord(
            patient_id=patient.patient_id,
            enrollment_date=patient.enrollment_date,
            first_event_type=first_event.event_type if first_event else None,
            first_event_date=first_event.event_date if first_event else None,
            days_to_first_event=first_event.days_from_enrollment if first_event else None,
            event_count=total_events,
            all_events=events,
        )
        
        return followup
