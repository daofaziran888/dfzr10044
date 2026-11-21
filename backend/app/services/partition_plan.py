"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PartitionPlanService(BaseModuleService):
    MODULE = "partition_plan"
    ENTITY = "分区方案"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["方案编号", "所属湖表", "分区键", "分区粒度", "预期分区数", "单分区行数", "冷热判定", "最近评估"]
    REQUIRED_FIELDS = ["方案编号", "所属湖表", "分区键"]
    STATUS_ORDER = ["草稿", "评估中", "已采纳", "已驳回"]
    ACTION_RULES = {"提交评估": "评估中", "采纳方案": "已采纳", "驳回方案": "已驳回"}
    NEGATIVE_ACTIONS = ["驳回方案"]
