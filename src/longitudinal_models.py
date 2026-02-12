"""
纵向数据模型 - 支持多时间点随访数据
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, validator, Field


class TimePointData(BaseModel):
    """单个时间点的随访数据"""

    time_point: str = Field(..., description="时间点名称，如'第三个月随访'")
    months: int = Field(..., description="距离入组的月数，如3, 6, 12等")
    visit_date: Optional[date] = Field(None, description="实际随访日期")
    is_lost_to_followup: bool = Field(default=False, description="是否失访")
    loss_reason: Optional[str] = Field(None, description="失访原因")
    death_date: Optional[date] = Field(None, description="死亡日期")
    death_reason: Optional[str] = Field(None, description="死亡原因")
    cardiovascular_event: Optional[str] = Field(None, description="心血管不良事件")
    event_types: List[str] = Field(
        default_factory=list, description="解析后的事件类型列表，如['angina', 'hospitalization']"
    )
    coronary_intervention: Optional[str] = Field(None, description="冠脉干预治疗")
    intervention_date: Optional[date] = Field(None, description="干预治疗日期")
    coronary_bypass: Optional[str] = Field(None, description="冠脉搭桥")
    bypass_date: Optional[date] = Field(None, description="冠脉搭桥日期")
    revascularization_treatment: Optional[str] = Field(None, description="血运重建治疗")
    revascularization_type: Optional[str] = Field(None, description="血运重建治疗类型")
    revascularization_date: Optional[date] = Field(None, description="血运重建治疗日期")
    revascularization_detail: Optional[str] = Field(None, description="血运重建治疗详细说明")
    current_symptoms: Optional[str] = Field(None, description="当前症状")
    current_diagnosis: Optional[str] = Field(None, description="当前诊断")
    notes: Optional[str] = Field(None, description="备注")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="原始数据")

    class Config:
        json_encoders = {date: lambda v: v.isoformat() if v else None}


class LongitudinalPatientRecord(BaseModel):
    """纵向患者记录 - 包含多个时间点的数据"""

    patient_id: str = Field(..., description="患者ID")
    patient_name: Optional[str] = Field(None, description="患者姓名")
    enrollment_date: date = Field(..., description="入组日期")
    birthday: Optional[date] = Field(None, description="出生日期")
    age: Optional[int] = Field(None, description="入组时年龄")
    gender: Optional[str] = Field(None, description="性别")
    group_name: Optional[str] = Field(None, description="分组名称")

    # 多时间点数据
    time_points: List[TimePointData] = Field(
        default_factory=list, description="所有时间点的随访数据"
    )

    # 统计信息
    latest_followup_date: Optional[date] = Field(None, description="最晚随访日期")
    latest_followup_months: Optional[int] = Field(None, description="最晚随访距离入组的月数")
    days_to_latest_followup: Optional[int] = Field(None, description="最晚随访距离入组的天数")

    # 事件信息
    first_event_type: Optional[str] = Field(None, description="首次事件类型")
    first_event_date: Optional[date] = Field(None, description="首次事件日期")
    first_event_time_point: Optional[str] = Field(None, description="首次事件所在时间点")
    days_to_first_event: Optional[int] = Field(None, description="首次事件距离入组的天数")

    # 其他事件统计
    has_death: bool = Field(default=False, description="是否有死亡事件")
    has_cardiovascular_event: bool = Field(default=False, description="是否有心血管不良事件")
    has_lost_to_followup: bool = Field(default=False, description="是否有失访")

    raw_data: Dict[str, Any] = Field(default_factory=dict, description="原始数据")

    class Config:
        json_encoders = {date: lambda v: v.isoformat() if v else None}

    def to_followup_dict(self) -> Dict[str, Any]:
        """转换为随访记录字典用于导出"""
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "age": self.age,
            "gender": self.gender,
            "group_name": self.group_name,
            "latest_followup_date": (
                self.latest_followup_date.isoformat() if self.latest_followup_date else None
            ),
            "latest_followup_months": self.latest_followup_months,
            "days_to_latest_followup": self.days_to_latest_followup,
            "first_event_type": self.first_event_type,
            "first_event_date": (
                self.first_event_date.isoformat() if self.first_event_date else None
            ),
            "days_to_first_event": self.days_to_first_event,
            "has_death": self.has_death,
            "has_cardiovascular_event": self.has_cardiovascular_event,
            "has_lost_to_followup": self.has_lost_to_followup,
            "first_event_time_point": self.first_event_time_point,
        }


class LongitudinalFollowupRecord(BaseModel):
    """纵向随访记录 - 最终输出"""

    patient_id: str = Field(..., description="患者ID")
    patient_name: Optional[str] = Field(None, description="患者姓名")
    enrollment_date: date = Field(..., description="入组日期")
    birthday: Optional[date] = Field(None, description="出生日期")

    # 随访时间信息
    latest_followup_date: Optional[date] = Field(None, description="最晚随访日期")
    latest_followup_months: Optional[int] = Field(None, description="最晚随访月数")
    days_to_latest_followup: Optional[int] = Field(None, description="最晚随访距离入组天数")

    # 首次事件信息（整体）
    first_event_type: Optional[str] = Field(None, description="首次事件类型")
    first_event_date: Optional[date] = Field(None, description="首次事件日期")
    first_event_time_point: Optional[str] = Field(None, description="首次事件时间点")
    first_event_months: Optional[int] = Field(None, description="首次事件月数")
    days_to_first_event: Optional[int] = Field(None, description="首次事件距离入组天数")

    # 各类事件的首次发生信息
    first_death_date: Optional[date] = Field(None, description="首次死亡日期")
    first_death_time_point: Optional[str] = Field(None, description="首次死亡时间点")
    days_to_first_death: Optional[int] = Field(None, description="首次死亡距入组天数")

    first_mi_date: Optional[date] = Field(None, description="首次心肌梗死日期")
    first_mi_time_point: Optional[str] = Field(None, description="首次MI时间点")
    days_to_first_mi: Optional[int] = Field(None, description="首次MI距入组天数")

    first_angina_date: Optional[date] = Field(None, description="首次心绞痛日期")
    first_angina_time_point: Optional[str] = Field(None, description="首次心绞痛时间点")
    days_to_first_angina: Optional[int] = Field(None, description="首次心绞痛距入组天数")

    first_heart_failure_date: Optional[date] = Field(None, description="首次心衰日期")
    first_heart_failure_time_point: Optional[str] = Field(None, description="首次心衰时间点")
    days_to_first_heart_failure: Optional[int] = Field(None, description="首次心衰距入组天数")

    first_revascularization_date: Optional[date] = Field(None, description="首次血运重建日期")
    first_revascularization_time_point: Optional[str] = Field(
        None, description="首次血运重建时间点"
    )
    days_to_first_revascularization: Optional[int] = Field(
        None, description="首次血运重建距入组天数"
    )

    first_hospitalization_date: Optional[date] = Field(None, description="首次因心脏病入院日期")
    first_hospitalization_time_point: Optional[str] = Field(None, description="首次入院时间点")
    days_to_first_hospitalization: Optional[int] = Field(None, description="首次入院距入组天数")

    # 冠脉相关检查/治疗记录
    has_coronary_ct: bool = Field(default=False, description="是否有冠脉CT")
    first_coronary_ct_date: Optional[date] = Field(None, description="首次冠脉CT日期")
    first_coronary_ct_time_point: Optional[str] = Field(None, description="首次冠脉CT时间点")

    has_coronary_angiography: bool = Field(default=False, description="是否有冠脉造影")
    first_coronary_angiography_date: Optional[date] = Field(None, description="首次冠脉造影日期")
    first_coronary_angiography_time_point: Optional[str] = Field(
        None, description="首次冠脉造影时间点"
    )

    has_coronary_intervention: bool = Field(default=False, description="是否有介入治疗")
    first_coronary_intervention_date: Optional[date] = Field(None, description="首次介入治疗日期")
    first_coronary_intervention_time_point: Optional[str] = Field(
        None, description="首次介入治疗时间点"
    )

    has_coronary_bypass: bool = Field(default=False, description="是否有冠脉搭桥")
    first_coronary_bypass_date: Optional[date] = Field(None, description="首次冠脉搭桥日期")
    first_coronary_bypass_time_point: Optional[str] = Field(None, description="首次冠脉搭桥时间点")

    has_revascularization_treatment: bool = Field(default=False, description="是否有血运重建治疗")
    first_revascularization_treatment_date: Optional[date] = Field(
        None, description="首次血运重建治疗日期"
    )
    first_revascularization_treatment_time_point: Optional[str] = Field(
        None, description="首次血运重建治疗时间点"
    )
    first_revascularization_treatment_type: Optional[str] = Field(
        None, description="首次血运重建治疗类型"
    )
    first_revascularization_treatment_detail: Optional[str] = Field(
        None, description="首次血运重建治疗详情"
    )

    # 事件统计
    has_death: bool = Field(default=False, description="是否死亡")
    has_cardiovascular_event: bool = Field(default=False, description="是否有心血管不良事件")
    has_lost_to_followup: bool = Field(default=False, description="是否失访")

    # 其他信息
    age: Optional[int] = Field(None, description="入组时年龄")
    gender: Optional[str] = Field(None, description="性别")
    group_name: Optional[str] = Field(None, description="分组")

    # 随访状态总结
    total_followup_status: str = Field(default="unknown", description="总体随访状态")

    # 生存分析字段
    event_occurred: Optional[int] = Field(None, description="事件指示：1=事件发生，0=删失")
    survival_time_days: Optional[int] = Field(None, description="用于生存分析的时间（天）")
    endpoint_event: Optional[str] = Field(
        None, description="生存分析终点事件类型（death/mace/mi/any_event等）"
    )

    processing_timestamp: datetime = Field(default_factory=datetime.now, description="处理时间戳")

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            datetime: lambda v: v.isoformat(),
        }

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.dict()

    def to_flattened_dict(self) -> Dict[str, Any]:
        """转换为展平的字典（用于导出表格）"""
        return {
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "age": self.age,
            "gender": self.gender,
            "group_name": self.group_name,
            "enrollment_date": self.enrollment_date.isoformat(),
            "latest_followup_date": (
                self.latest_followup_date.isoformat() if self.latest_followup_date else None
            ),
            "latest_followup_months": self.latest_followup_months,
            "days_to_latest_followup": self.days_to_latest_followup,
            "first_event_type": self.first_event_type,
            "first_event_date": (
                self.first_event_date.isoformat() if self.first_event_date else None
            ),
            "first_event_time_point": self.first_event_time_point,
            "first_event_months": self.first_event_months,
            "days_to_first_event": self.days_to_first_event,
            # 各类事件首次发生信息
            "first_death_date": (
                self.first_death_date.isoformat() if self.first_death_date else None
            ),
            "first_death_time_point": self.first_death_time_point,
            "days_to_first_death": self.days_to_first_death,
            "first_mi_date": self.first_mi_date.isoformat() if self.first_mi_date else None,
            "first_mi_time_point": self.first_mi_time_point,
            "days_to_first_mi": self.days_to_first_mi,
            "first_angina_date": (
                self.first_angina_date.isoformat() if self.first_angina_date else None
            ),
            "first_angina_time_point": self.first_angina_time_point,
            "days_to_first_angina": self.days_to_first_angina,
            "first_heart_failure_date": (
                self.first_heart_failure_date.isoformat() if self.first_heart_failure_date else None
            ),
            "first_heart_failure_time_point": self.first_heart_failure_time_point,
            "days_to_first_heart_failure": self.days_to_first_heart_failure,
            "first_revascularization_date": (
                self.first_revascularization_date.isoformat()
                if self.first_revascularization_date
                else None
            ),
            "first_revascularization_time_point": self.first_revascularization_time_point,
            "days_to_first_revascularization": self.days_to_first_revascularization,
            "first_hospitalization_date": (
                self.first_hospitalization_date.isoformat()
                if self.first_hospitalization_date
                else None
            ),
            "first_hospitalization_time_point": self.first_hospitalization_time_point,
            "days_to_first_hospitalization": self.days_to_first_hospitalization,
            # 冠脉相关
            "has_coronary_ct": self.has_coronary_ct,
            "first_coronary_ct_date": (
                self.first_coronary_ct_date.isoformat() if self.first_coronary_ct_date else None
            ),
            "first_coronary_ct_time_point": self.first_coronary_ct_time_point,
            "has_coronary_angiography": self.has_coronary_angiography,
            "first_coronary_angiography_date": (
                self.first_coronary_angiography_date.isoformat()
                if self.first_coronary_angiography_date
                else None
            ),
            "first_coronary_angiography_time_point": self.first_coronary_angiography_time_point,
            "has_coronary_intervention": self.has_coronary_intervention,
            "first_coronary_intervention_date": (
                self.first_coronary_intervention_date.isoformat()
                if self.first_coronary_intervention_date
                else None
            ),
            "first_coronary_intervention_time_point": self.first_coronary_intervention_time_point,
            "has_coronary_bypass": self.has_coronary_bypass,
            "first_coronary_bypass_date": (
                self.first_coronary_bypass_date.isoformat()
                if self.first_coronary_bypass_date
                else None
            ),
            "first_coronary_bypass_time_point": self.first_coronary_bypass_time_point,
            "has_revascularization_treatment": self.has_revascularization_treatment,
            "first_revascularization_treatment_date": (
                self.first_revascularization_treatment_date.isoformat()
                if self.first_revascularization_treatment_date
                else None
            ),
            "first_revascularization_treatment_time_point": self.first_revascularization_treatment_time_point,
            "first_revascularization_treatment_type": self.first_revascularization_treatment_type,
            "first_revascularization_treatment_detail": self.first_revascularization_treatment_detail,
            # 布尔统计
            "has_death": self.has_death,
            "has_cardiovascular_event": self.has_cardiovascular_event,
            "has_lost_to_followup": self.has_lost_to_followup,
            "total_followup_status": self.total_followup_status,
            # Survival analysis fields
            "event_occurred": getattr(self, "event_occurred", None),
            "survival_time_days": getattr(self, "survival_time_days", None),
            "endpoint_event": getattr(self, "endpoint_event", None),
            "processing_timestamp": self.processing_timestamp.isoformat(),
        }
