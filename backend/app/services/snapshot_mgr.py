"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SnapshotMgrService(BaseModuleService):
    MODULE = "snapshot_mgr"
    ENTITY = "湖表快照"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["快照编号", "所属湖表", "快照标识", "父快照", "新增行数", "删除行数", "文件清单摘要", "生成时间"]
    REQUIRED_FIELDS = ["快照编号", "所属湖表", "快照标识"]
    STATUS_ORDER = ["生成中", "可用", "已过期", "已回退"]
    ACTION_RULES = {"标记可用": "可用", "标记过期": "已过期", "执行回退": "已回退"}
    NEGATIVE_ACTIONS = []
