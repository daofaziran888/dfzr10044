"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PartitionEvolveService(BaseModuleService):
    MODULE = "partition_evolve"
    ENTITY = "演化记录"
    OPERATION_TERM = "水位"
    LIST_FIELDS = ["演化编号", "所属湖表", "原分区键", "新分区键", "影响分区数", "历史数据处置", "切换水位", "演化时间"]
    REQUIRED_FIELDS = ["演化编号", "所属湖表", "原分区键"]
    STATUS_ORDER = ["待切换", "双分区并存", "已完成", "已回退"]
    ACTION_RULES = {"启动演化": "双分区并存", "确认完成": "已完成", "执行回退": "已回退"}
    NEGATIVE_ACTIONS = []
