"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ExpirePolicyService(BaseModuleService):
    MODULE = "expire_policy"
    ENTITY = "过期策略"
    OPERATION_TERM = "查询"
    LIST_FIELDS = ["策略编号", "所属湖表", "保留快照数", "保留天数", "受保护标签", "清理范围", "最近清理", "释放字节数"]
    REQUIRED_FIELDS = ["策略编号", "所属湖表", "保留快照数"]
    STATUS_ORDER = ["草稿", "已生效", "清理中", "已暂停"]
    ACTION_RULES = {"启效策略": "已生效", "启动清理": "清理中", "暂停策略": "已暂停"}
    NEGATIVE_ACTIONS = []
