"""
纵向事件处理模块 - 处理跨多个时间点的事件追踪
"""

import logging
from typing import List, Optional, Tuple, Dict
from datetime import date

from .longitudinal_models import (
    LongitudinalPatientRecord,
    TimePointData,
    LongitudinalFollowupRecord,
)
from .logger import setup_logger

logger = logging.getLogger(__name__)


class LongitudinalEventProcessor:
    """纵向事件处理器 - 从多个时间点的数据中识别和追踪事件"""

    # 事件优先级（按严重程度排序）
    EVENT_PRIORITY = [
        "death",  # 最高优先级
        "cardiovascular_event",
        "coronary_intervention",
        "coronary_bypass",
        "other",
    ]

    # 事件类型关键字映射
    EVENT_TYPE_KEYWORDS = {
        "death": ["死亡", "death", "deceased"],
        "cardiovascular_event": [
            "心血管",
            "cardiovascular",
            "事件",
            "event",
            "acute",
            "myocardial",
            "infarction",
            "stroke",
            "unstable",
        ],
        "coronary_intervention": [
            "冠脉",
            "coronary",
            "intervention",
            "angiography",
            "stent",
            "angioplasty",
            "介入",
        ],
        "coronary_bypass": ["搭桥", "bypass", "CABG"],
    }

    # 码表映射 (基于随访编码.xlsx)
    # 随访期间心血管不良事件: 1=有, 2=无
    CARDIOVASCULAR_EVENT_CODES = {
        1: "有",
        1.0: "有",
        2: "无",
        2.0: "无",
    }

    # 如有不良事件，何事件: 具体事件类型编码
    ADVERSE_EVENT_TYPE_CODES = {
        1: "cardiac_death",  # 心源性死亡
        1.0: "cardiac_death",
        2: "nonfatal_mi",  # 非致死性心肌梗死
        2.0: "nonfatal_mi",
        3: "target_vessel_revascularization",  # 靶病变血运重建
        3.0: "target_vessel_revascularization",
        4: "heart_failure",  # 心衰发作
        4.0: "heart_failure",
        5: "angina",  # 心绞痛
        5.0: "angina",
        6: "cardiac_hospitalization",  # 因心脏病入院
        6.0: "cardiac_hospitalization",
    }

    # 死亡原因编码
    DEATH_REASON_CODES = {
        1: "因心血管原因死亡",
        1.0: "因心血管原因死亡",
        2: "因非心血管原因死亡",
        2.0: "因非心血管原因死亡",
        3: "死因不详",
        3.0: "死因不详",
    }

    def __init__(self, endpoint: str = "death"):
        """
        初始化事件处理器

        Args:
            endpoint: 生存分析终点事件类型
                - 'death': 死亡（默认）
                - 'mace': 主要不良心血管事件（MACE: 死亡+MI+血运重建）
                - 'mi': 心肌梗死
                - 'angina': 心绞痛
                - 'heart_failure': 心衰
                - 'revascularization': 血运重建
                - 'hospitalization': 因心脏病住院
                - 'any_event': 任何事件
        """
        self.endpoint = endpoint.lower()

    def process_followup(
        self, patient_record: LongitudinalPatientRecord
    ) -> LongitudinalFollowupRecord:
        """
        处理患者的纵向随访数据，识别所有事件类型并记录各自首次发生时间

        Args:
            patient_record: 纵向患者记录

        Returns:
            纵向随访记录（最终输出格式）
        """
        # 初始化追踪变量（整体首次事件）
        first_event_type: Optional[str] = None
        first_event_time_point: Optional[str] = None
        first_event_date: Optional[date] = None
        first_event_months: Optional[int] = None

        # 各类事件的首次发生追踪
        event_tracking = {
            "death": {"date": None, "time_point": None, "days": None},
            "cardiac_death": {"date": None, "time_point": None, "days": None},
            "mi": {"date": None, "time_point": None, "days": None},  # 新增：直接支持'mi'
            "nonfatal_mi": {"date": None, "time_point": None, "days": None},
            "angina": {"date": None, "time_point": None, "days": None},
            "heart_failure": {"date": None, "time_point": None, "days": None},
            "revascularization": {"date": None, "time_point": None, "days": None},  # 新增
            "target_vessel_revascularization": {"date": None, "time_point": None, "days": None},
            "hospitalization": {"date": None, "time_point": None, "days": None},  # 新增
            "cardiac_hospitalization": {"date": None, "time_point": None, "days": None},
        }

        # 冠脉相关检查/治疗追踪
        coronary_tracking = {
            "coronary_ct": {"date": None, "time_point": None, "has": False},
            "coronary_angiography": {"date": None, "time_point": None, "has": False},
            "coronary_intervention": {"date": None, "time_point": None, "has": False},
            "coronary_bypass": {"date": None, "time_point": None, "has": False},
            "revascularization_treatment": {
                "date": None,
                "time_point": None,
                "has": False,
                "type": None,
                "detail": None,
            },
        }

        # 按时间点月数排序
        sorted_time_points = sorted(patient_record.time_points, key=lambda tp: tp.months)

        # 遍历所有时间点，识别所有事件
        for time_point in sorted_time_points:
            # 识别该时间点的所有事件（可能有多个）
            events_list = self._identify_all_events(time_point)

            for event_type, event_date in events_list:
                if event_type and event_date:
                    # 计算距入组天数
                    days_to_event = None
                    if patient_record.enrollment_date:
                        days_to_event = (event_date - patient_record.enrollment_date).days

                    # 更新该事件类型的首次发生（如果尚未记录）
                    if event_type in event_tracking and event_tracking[event_type]["date"] is None:
                        event_tracking[event_type]["date"] = event_date
                        event_tracking[event_type]["time_point"] = time_point.time_point
                        event_tracking[event_type]["days"] = days_to_event

                        logger.debug(
                            f"患者{patient_record.patient_id}: "
                            f"{event_type} @ {time_point.time_point} ({event_date})"
                        )

                    # 更新整体首次事件（任意类型的最早事件）
                    if first_event_date is None or event_date < first_event_date:
                        first_event_type = event_type
                        first_event_time_point = time_point.time_point
                        first_event_date = event_date
                        first_event_months = time_point.months

            # 追踪冠脉相关检查/治疗（从raw_data或字段中提取）
            self._track_coronary_procedures(
                time_point, coronary_tracking, patient_record.enrollment_date
            )

        # 计算整体首次事件距入组天数
        days_to_first_event: Optional[int] = None
        if first_event_date is not None and patient_record.enrollment_date is not None:
            delta = first_event_date - patient_record.enrollment_date
            days_to_first_event = delta.days

        # 根据指定的终点事件计算生存结局
        endpoint_occurred, survival_time, endpoint_desc = self._calculate_endpoint_outcome(
            event_tracking, patient_record.enrollment_date, patient_record.latest_followup_date
        )

        # 向后兼容：保留原有的任意事件标志（用于has_event等字段）
        event_flag = any(v["date"] is not None for v in event_tracking.values())

        # 创建最终随访记录
        followup_record = LongitudinalFollowupRecord(
            patient_id=patient_record.patient_id,
            patient_name=patient_record.patient_name,
            enrollment_date=patient_record.enrollment_date,
            birthday=patient_record.birthday,
            age=patient_record.age,
            gender=patient_record.gender,
            group_name=patient_record.group_name,
            latest_followup_date=patient_record.latest_followup_date,
            latest_followup_months=patient_record.latest_followup_months,
            days_to_latest_followup=patient_record.days_to_latest_followup,
            first_event_type=first_event_type,
            first_event_date=first_event_date,
            first_event_time_point=first_event_time_point,
            first_event_months=first_event_months,
            days_to_first_event=days_to_first_event,
            # 各类事件首次发生信息
            first_death_date=event_tracking["death"]["date"]
            or event_tracking["cardiac_death"]["date"],
            first_death_time_point=event_tracking["death"]["time_point"]
            or event_tracking["cardiac_death"]["time_point"],
            days_to_first_death=event_tracking["death"]["days"]
            or event_tracking["cardiac_death"]["days"],
            first_mi_date=event_tracking["mi"]["date"] or event_tracking["nonfatal_mi"]["date"],
            first_mi_time_point=event_tracking["mi"]["time_point"]
            or event_tracking["nonfatal_mi"]["time_point"],
            days_to_first_mi=event_tracking["mi"]["days"] or event_tracking["nonfatal_mi"]["days"],
            first_angina_date=event_tracking["angina"]["date"],
            first_angina_time_point=event_tracking["angina"]["time_point"],
            days_to_first_angina=event_tracking["angina"]["days"],
            first_heart_failure_date=event_tracking["heart_failure"]["date"],
            first_heart_failure_time_point=event_tracking["heart_failure"]["time_point"],
            days_to_first_heart_failure=event_tracking["heart_failure"]["days"],
            first_revascularization_date=event_tracking["revascularization"]["date"]
            or event_tracking["target_vessel_revascularization"]["date"],
            first_revascularization_time_point=event_tracking["revascularization"]["time_point"]
            or event_tracking["target_vessel_revascularization"]["time_point"],
            days_to_first_revascularization=event_tracking["revascularization"]["days"]
            or event_tracking["target_vessel_revascularization"]["days"],
            first_hospitalization_date=event_tracking["hospitalization"]["date"]
            or event_tracking["cardiac_hospitalization"]["date"],
            first_hospitalization_time_point=event_tracking["hospitalization"]["time_point"]
            or event_tracking["cardiac_hospitalization"]["time_point"],
            days_to_first_hospitalization=event_tracking["hospitalization"]["days"]
            or event_tracking["cardiac_hospitalization"]["days"],
            # 冠脉相关检查/治疗
            has_coronary_ct=coronary_tracking["coronary_ct"]["has"],
            first_coronary_ct_date=coronary_tracking["coronary_ct"]["date"],
            first_coronary_ct_time_point=coronary_tracking["coronary_ct"]["time_point"],
            has_coronary_angiography=coronary_tracking["coronary_angiography"]["has"],
            first_coronary_angiography_date=coronary_tracking["coronary_angiography"]["date"],
            first_coronary_angiography_time_point=coronary_tracking["coronary_angiography"][
                "time_point"
            ],
            has_coronary_intervention=coronary_tracking["coronary_intervention"]["has"],
            first_coronary_intervention_date=coronary_tracking["coronary_intervention"]["date"],
            first_coronary_intervention_time_point=coronary_tracking["coronary_intervention"][
                "time_point"
            ],
            has_coronary_bypass=coronary_tracking["coronary_bypass"]["has"],
            first_coronary_bypass_date=coronary_tracking["coronary_bypass"]["date"],
            first_coronary_bypass_time_point=coronary_tracking["coronary_bypass"]["time_point"],
            has_revascularization_treatment=coronary_tracking["revascularization_treatment"]["has"],
            first_revascularization_treatment_date=coronary_tracking["revascularization_treatment"][
                "date"
            ],
            first_revascularization_treatment_time_point=coronary_tracking[
                "revascularization_treatment"
            ]["time_point"],
            first_revascularization_treatment_type=coronary_tracking["revascularization_treatment"][
                "type"
            ],
            first_revascularization_treatment_detail=coronary_tracking[
                "revascularization_treatment"
            ]["detail"],
            event_occurred=endpoint_occurred,
            survival_time_days=survival_time,
            endpoint_event=endpoint_desc,
            total_followup_status=self._determine_followup_status(patient_record),
        )

        return followup_record

    def _calculate_endpoint_outcome(
        self, event_tracking: Dict, enrollment_date: date, latest_date: date
    ) -> Tuple[bool, int, str]:
        """
        根据选定的终点事件计算生存结局

        Args:
            event_tracking: 事件追踪字典
            enrollment_date: 入组日期
            latest_date: 最后随访日期

        Returns:
            (是否发生终点事件, 生存时间天数, 终点事件描述)
        """
        endpoint_occurred = False
        endpoint_date = None
        endpoint_description = self.endpoint

        if self.endpoint == "death":
            # 死亡为终点
            if event_tracking["death"]["date"] or event_tracking["cardiac_death"]["date"]:
                endpoint_occurred = True
                endpoint_date = (
                    event_tracking["death"]["date"] or event_tracking["cardiac_death"]["date"]
                )

        elif self.endpoint == "mace":
            # MACE: 死亡 + MI + 血运重建
            mace_dates = []
            if event_tracking["death"]["date"]:
                mace_dates.append(event_tracking["death"]["date"])
            if event_tracking["cardiac_death"]["date"]:
                mace_dates.append(event_tracking["cardiac_death"]["date"])
            if event_tracking["nonfatal_mi"]["date"]:
                mace_dates.append(event_tracking["nonfatal_mi"]["date"])
            if event_tracking["target_vessel_revascularization"]["date"]:
                mace_dates.append(event_tracking["target_vessel_revascularization"]["date"])

            if mace_dates:
                endpoint_occurred = True
                endpoint_date = min(mace_dates)
                endpoint_description = "mace"

        elif self.endpoint == "mi":
            # 心肌梗死为终点
            if event_tracking["nonfatal_mi"]["date"]:
                endpoint_occurred = True
                endpoint_date = event_tracking["nonfatal_mi"]["date"]

        elif self.endpoint == "angina":
            # 心绞痛为终点
            if event_tracking["angina"]["date"]:
                endpoint_occurred = True
                endpoint_date = event_tracking["angina"]["date"]

        elif self.endpoint == "heart_failure":
            # 心衰为终点
            if event_tracking["heart_failure"]["date"]:
                endpoint_occurred = True
                endpoint_date = event_tracking["heart_failure"]["date"]

        elif self.endpoint == "revascularization":
            # 血运重建为终点
            if event_tracking["target_vessel_revascularization"]["date"]:
                endpoint_occurred = True
                endpoint_date = event_tracking["target_vessel_revascularization"]["date"]

        elif self.endpoint == "hospitalization":
            # 住院为终点
            if event_tracking["cardiac_hospitalization"]["date"]:
                endpoint_occurred = True
                endpoint_date = event_tracking["cardiac_hospitalization"]["date"]

        elif self.endpoint == "any_event":
            # 任何事件为终点（取最早发生的）
            all_dates = [v["date"] for v in event_tracking.values() if v["date"]]
            if all_dates:
                endpoint_occurred = True
                endpoint_date = min(all_dates)
                endpoint_description = "any_event"

        # 计算生存时间
        if endpoint_occurred and endpoint_date:
            survival_days = (endpoint_date - enrollment_date).days
        else:
            # 删失：使用最后随访日期
            if latest_date and enrollment_date:
                survival_days = (latest_date - enrollment_date).days
            else:
                survival_days = 0  # 无有效日期时设为0

        return endpoint_occurred, survival_days, endpoint_description

    def _identify_all_events(self, time_point: TimePointData) -> List[Tuple[str, date]]:
        """
        从单个时间点识别所有事件（可能有多个）

        Args:
            time_point: 时间点数据

        Returns:
            事件列表: [(事件类型, 事件日期), ...]
        """
        events = []

        # 1. 检查死亡（最高优先级 - 若有明确死亡日期）
        if time_point.death_date is not None:
            events.append(("death", time_point.death_date))
            return events  # 死亡后不再记录其它事件

        # 2. 检查event_types字段（新增）- 直接使用解析后的事件类型列表
        if time_point.event_types and time_point.visit_date:
            # event_types是一个列表，可能包含多个事件（如['angina', 'hospitalization']）
            for event_type in time_point.event_types:
                events.append((event_type, time_point.visit_date))

        # 3. 若没有解析的event_types，则检查"随访期间心血管不良事件"字段（向后兼容）
        if not events:
            cv_event_value = self._try_parse_code(time_point.cardiovascular_event)

            # 若 cardiovascular_event == 1 ("有事件")，则查看具体事件类型
            if cv_event_value is not None and cv_event_value in [1, 1.0]:
                adverse_event_code = self._get_adverse_event_code(time_point)

                if adverse_event_code is not None:
                    event_type_name = self.ADVERSE_EVENT_TYPE_CODES.get(adverse_event_code)
                    if event_type_name and time_point.visit_date:
                        events.append((event_type_name, time_point.visit_date))
                elif time_point.visit_date:
                    # 若无法识别具体事件类型，返回通用"cardiovascular_event"
                    events.append(("cardiovascular_event", time_point.visit_date))

        # 4. 检查冠脉搭桥（可能与上述事件并存）
        if time_point.coronary_bypass is not None:
            bypass_code = self._try_parse_code(time_point.coronary_bypass)
            if bypass_code in [1, 1.0]:
                bypass_date = time_point.bypass_date or time_point.visit_date
                if bypass_date:
                    events.append(("coronary_bypass", bypass_date))

        # 5. 检查冠脉介入
        if time_point.coronary_intervention is not None:
            interv_code = self._try_parse_code(time_point.coronary_intervention)
            if interv_code in [1, 1.0]:
                interv_date = time_point.intervention_date or time_point.visit_date
                if interv_date:
                    events.append(("coronary_intervention", interv_date))

        return events

    def _identify_event(self, time_point: TimePointData) -> Tuple[Optional[str], Optional[date]]:
        """
        从单个时间点识别事件（基于数字编码）

        Args:
            time_point: 时间点数据

        Returns:
            (事件类型, 事件日期) 或 (None, None)
        """
        # 1. 检查死亡（最高优先级 - 若有明确死亡日期）
        if time_point.death_date is not None:
            return ("death", time_point.death_date)

        # 2. 检查event_types字段（新增）- 直接使用解析后的事件类型
        if time_point.event_types:
            # 如果有多个事件，取第一个作为主要事件
            # 可以根据需要调整优先级（例如death > mi > angina等）
            event_type = time_point.event_types[0]
            return (event_type, time_point.visit_date)

        # 3. 检查"随访期间心血管不良事件"字段的数字编码（向后兼容）
        # cardiovascular_event 可能是字符串（如 "1.0" "2.0"）或数字
        cv_event_value = None
        if time_point.cardiovascular_event is not None:
            try:
                # 尝试转为字符串后解析为float再转int/float key
                val_str = str(time_point.cardiovascular_event).strip()
                if val_str:
                    cv_event_value = float(val_str)
            except (ValueError, AttributeError):
                # 若转换失败，尝试按关键字匹配（兼容旧逻辑）
                if self._contains_keywords(
                    str(time_point.cardiovascular_event), "cardiovascular_event"
                ):
                    return ("cardiovascular_event", time_point.visit_date)

        # 若 cardiovascular_event == 1 ("有事件")，但没有解析的event_types
        if cv_event_value is not None and cv_event_value in [1, 1.0]:
            # 查找"如有不良事件，何事件"字段（可能是raw_data中的其它列）
            # 在 TimePointData 模型里没有直接字段，需从 raw_data 获取
            adverse_event_code = self._get_adverse_event_code(time_point)

            if adverse_event_code is not None:
                event_type_name = self.ADVERSE_EVENT_TYPE_CODES.get(adverse_event_code)
                if event_type_name:
                    # 使用该时间点的visit_date作为事件日期
                    return (event_type_name, time_point.visit_date)

            # 若无法识别具体事件类型，返回通用"cardiovascular_event"
            return ("cardiovascular_event", time_point.visit_date)

        # 4. 若 cardiovascular_event == 2 ("无事件"), 继续检查其它字段（冠脉介入/搭桥）
        # 检查冠脉搭桥
        if time_point.coronary_bypass is not None:
            # 尝试按编码识别（若是数字）
            bypass_code = self._try_parse_code(time_point.coronary_bypass)
            if bypass_code in [1, 1.0]:  # 假设1表示"有搭桥"
                return ("coronary_bypass", time_point.bypass_date or time_point.visit_date)
            # 兼容旧逻辑：按关键字匹配
            if self._contains_keywords(str(time_point.coronary_bypass), "coronary_bypass"):
                return ("coronary_bypass", time_point.bypass_date or time_point.visit_date)

        # 检查冠脉介入
        if time_point.coronary_intervention is not None:
            interv_code = self._try_parse_code(time_point.coronary_intervention)
            if interv_code in [1, 1.0]:  # 假设1表示"有介入"
                return (
                    "coronary_intervention",
                    time_point.intervention_date or time_point.visit_date,
                )
            if self._contains_keywords(
                str(time_point.coronary_intervention), "coronary_intervention"
            ):
                return (
                    "coronary_intervention",
                    time_point.intervention_date or time_point.visit_date,
                )

        return (None, None)

    def _get_adverse_event_code(self, time_point: TimePointData):
        """
        从time_point的raw_data中提取"如有不良事件，何事件"字段的编码

        Args:
            time_point: 时间点数据

        Returns:
            数字编码或None
        """
        if not hasattr(time_point, "raw_data") or time_point.raw_data is None:
            return None

        # 字段可能是 '如有不良事件，何事件1' 或类似名称
        possible_keys = ["如有不良事件，何事件1", "如有不良事件，何事件", "adverse_event_type"]
        for key in possible_keys:
            if key in time_point.raw_data:
                val = time_point.raw_data[key]
                if val is not None:
                    return self._try_parse_code(val)
        return None

    def _try_parse_code(self, value) -> Optional[float]:
        """
        尝试将值转为数字编码

        Args:
            value: 任意类型的值

        Returns:
            float或None
        """
        if value is None:
            return None
        try:
            # pandas可能把数字读成np.float64或字符串
            val_str = str(value).strip()
            if val_str and val_str.lower() not in ["nan", "none", ""]:
                return float(val_str)
        except (ValueError, AttributeError):
            pass
        return None

    def _track_coronary_procedures(
        self, time_point: TimePointData, tracking: Dict, enrollment_date: Optional[date]
    ) -> None:
        """
        追踪冠脉相关检查/治疗的首次发生

        Args:
            time_point: 时间点数据
            tracking: 追踪字典
            enrollment_date: 入组日期
        """
        visit_date = time_point.visit_date
        if not visit_date:
            return

        # 检查coronary_intervention字段（可能包含CT/造影/介入的编码）
        if time_point.coronary_intervention is not None:
            interv_code = self._try_parse_code(time_point.coronary_intervention)
            # 1 = 有相关检查/治疗
            if interv_code in [1, 1.0]:
                # 尝试从raw_data中更细化识别具体类型
                # 这里简化处理：有coronary_intervention就记录为有造影/介入
                if not tracking["coronary_intervention"]["has"]:
                    tracking["coronary_intervention"]["has"] = True
                    tracking["coronary_intervention"]["date"] = (
                        time_point.intervention_date or visit_date
                    )
                    tracking["coronary_intervention"]["time_point"] = time_point.time_point

                # 同时标记可能有造影（因为介入通常需要造影）
                if not tracking["coronary_angiography"]["has"]:
                    tracking["coronary_angiography"]["has"] = True
                    tracking["coronary_angiography"]["date"] = (
                        time_point.intervention_date or visit_date
                    )
                    tracking["coronary_angiography"]["time_point"] = time_point.time_point

        # 检查coronary_bypass字段
        if time_point.coronary_bypass is not None:
            bypass_code = self._try_parse_code(time_point.coronary_bypass)
            if bypass_code in [1, 1.0]:
                if not tracking["coronary_bypass"]["has"]:
                    tracking["coronary_bypass"]["has"] = True
                    tracking["coronary_bypass"]["date"] = time_point.bypass_date or visit_date
                    tracking["coronary_bypass"]["time_point"] = time_point.time_point

        # 检查血运重建治疗字段
        if (
            hasattr(time_point, "revascularization_treatment")
            and time_point.revascularization_treatment is not None
        ):
            revasc_code = self._try_parse_code(time_point.revascularization_treatment)
            if revasc_code in [1, 1.0]:
                if not tracking["revascularization_treatment"]["has"]:
                    tracking["revascularization_treatment"]["has"] = True
                    tracking["revascularization_treatment"]["date"] = (
                        time_point.revascularization_date or visit_date
                    )
                    tracking["revascularization_treatment"]["time_point"] = time_point.time_point
                    tracking["revascularization_treatment"]["type"] = (
                        time_point.revascularization_type
                        if hasattr(time_point, "revascularization_type")
                        else None
                    )
                    tracking["revascularization_treatment"]["detail"] = (
                        time_point.revascularization_detail
                        if hasattr(time_point, "revascularization_detail")
                        else None
                    )

        # 从raw_data中尝试提取CT相关字段（如果有单独的CT字段）
        if hasattr(time_point, "raw_data") and time_point.raw_data:
            # 寻找可能的CT字段名
            ct_keys = [k for k in time_point.raw_data.keys() if "CT" in k or "ct" in k.lower()]
            for key in ct_keys:
                val = time_point.raw_data[key]
                ct_code = self._try_parse_code(val)
                if ct_code in [1, 1.0]:
                    if not tracking["coronary_ct"]["has"]:
                        tracking["coronary_ct"]["has"] = True
                        tracking["coronary_ct"]["date"] = visit_date
                        tracking["coronary_ct"]["time_point"] = time_point.time_point
                    break

    def _contains_keywords(self, text: str, event_type: str) -> bool:
        """
        检查文本是否包含特定事件类型的关键词

        Args:
            text: 文本内容
            event_type: 事件类型

        Returns:
            是否包含相关关键词
        """
        if not text:
            return False

        keywords = self.EVENT_TYPE_KEYWORDS.get(event_type, [])
        text_lower = text.lower()

        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True

        return False

    def _determine_followup_status(self, patient_record: LongitudinalPatientRecord) -> str:
        """
        确定患者的随访状态

        Args:
            patient_record: 纵向患者记录

        Returns:
            随访状态字符串
        """
        if not patient_record.time_points:
            return "no_data"

        # 检查是否失访
        for time_point in patient_record.time_points:
            if time_point.is_lost_to_followup:
                return "lost_to_followup"

        # 检查最晚随访时间点
        if patient_record.latest_followup_months is not None:
            if patient_record.latest_followup_months >= 60:
                return "complete"
            elif patient_record.latest_followup_months >= 12:
                return "adequate"
            else:
                return "incomplete"

        return "unknown"

    def process_batch(
        self, patient_records: List[LongitudinalPatientRecord]
    ) -> List[LongitudinalFollowupRecord]:
        """
        批量处理多个患者的纵向随访数据

        Args:
            patient_records: 患者记录列表

        Returns:
            最终随访记录列表
        """
        followup_records: List[LongitudinalFollowupRecord] = []

        logger.info(f"开始处理{len(patient_records)}个患者的事件数据...")

        for patient_record in patient_records:
            try:
                record = self.process_followup(patient_record)
                followup_records.append(record)
            except Exception as e:
                logger.error(f"处理患者{patient_record.patient_id}时出错: {e}")
                continue

        logger.info(f"成功处理{len(followup_records)}个患者")
        return followup_records
