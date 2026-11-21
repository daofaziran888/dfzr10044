"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class RebuildBackfillService(BaseModuleService):
    MODULE = "rebuild_backfill"
    ENTITY = "补数任务"
    OPERATION_TERM = "水位"
    LIST_FIELDS = ["补数编号", "所属湖表", "补数窗口", "依赖上游表", "重算分区数", "覆盖策略", "补数水位", "补数耗时"]
    REQUIRED_FIELDS = ["补数编号", "所属湖表", "补数窗口"]
    STATUS_ORDER = ["待排期", "补数中", "已补齐", "补数失败"]
    ACTION_RULES = {"排期补数": "补数中", "确认补齐": "已补齐", "标记失败": "补数失败"}
    NEGATIVE_ACTIONS = []
