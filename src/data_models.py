"""
数据模型定义
使用 Pydantic 进行数据验证
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, validator, Field


class EventInfo(BaseModel):
    """事件信息模型"""
    event_type: str = Field(..., description="事件类型")
    event_date: date = Field(..., description="事件发生日期")
    days_from_enrollment: int = Field(..., description="距离入组时间的天数")
    data_source: Optional[str] = Field(None, description="数据来源字段")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class PatientRecord(BaseModel):
    """患者基本信息模型"""
    patient_id: str = Field(..., description="患者ID")
    enrollment_date: date = Field(..., description="入组日期")
    age: Optional[int] = Field(None, description="入组时年龄")
    gender: Optional[str] = Field(None, description="性别")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="原始数据")
    
    @validator('enrollment_date')
    def validate_date(cls, v):
        """验证日期不在未来"""
        if isinstance(v, str):
            v = datetime.fromisoformat(v).date()
        if v > datetime.now().date():
            raise ValueError("入组日期不能在未来")
        return v
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class FollowupRecord(BaseModel):
    """随访记录模型 - 最终输出结果"""
    patient_id: str = Field(..., description="患者ID")
    enrollment_date: date = Field(..., description="入组日期")
    first_event_type: Optional[str] = Field(None, description="首次事件类型")
    first_event_date: Optional[date] = Field(None, description="首次事件日期")
    days_to_first_event: Optional[int] = Field(None, description="首次事件距离入组时间的天数")
    event_count: int = Field(default=0, description="事件总数")
    all_events: List[EventInfo] = Field(default_factory=list, description="所有事件列表")
    notes: Optional[str] = Field(None, description="备注")
    processing_timestamp: datetime = Field(default_factory=datetime.now, description="处理时间戳")
    
    @validator('days_to_first_event')
    def validate_days(cls, v):
        """验证天数非负"""
        if v is not None and v < 0:
            raise ValueError("天数不能为负")
        return v
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()
    
    def to_flattened_dict(self) -> Dict[str, Any]:
        """转换为展平的字典 (用于导出表格)"""
        return {
            'patient_id': self.patient_id,
            'enrollment_date': self.enrollment_date.isoformat(),
            'first_event_type': self.first_event_type,
            'first_event_date': self.first_event_date.isoformat() if self.first_event_date else None,
            'days_to_first_event': self.days_to_first_event,
            'event_count': self.event_count,
            'notes': self.notes,
            'processing_timestamp': self.processing_timestamp.isoformat(),
        }
