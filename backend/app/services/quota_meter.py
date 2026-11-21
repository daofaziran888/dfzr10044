"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QuotaMeterService(BaseModuleService):
    MODULE = "quota_meter"
    ENTITY = "额度读数"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["读数编号", "所属湖表", "额度类型", "已用额度", "额度上限", "计量窗口", "超额处置", "计量时间"]
    REQUIRED_FIELDS = ["读数编号", "所属湖表", "额度类型"]
    STATUS_ORDER = ["计量中", "已结算", "超额告警", "已冻结"]
    ACTION_RULES = {"确认结算": "已结算", "标记超额": "超额告警", "冻结额度": "已冻结"}
    NEGATIVE_ACTIONS = []
