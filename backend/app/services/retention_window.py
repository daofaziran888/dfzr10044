"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class RetentionWindowService(BaseModuleService):
    MODULE = "retention_window"
    ENTITY = "保留窗口"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["窗口编号", "所属湖表", "保留粒度", "保留周期", "到期分区数", "受审计标记", "回收字节数", "最近回收"]
    REQUIRED_FIELDS = ["窗口编号", "所属湖表", "保留粒度"]
    STATUS_ORDER = ["生效中", "即将到期", "已回收", "已暂停"]
    ACTION_RULES = {"确认生效": "即将到期", "启动回收": "已回收", "暂停窗口": "已暂停"}
    NEGATIVE_ACTIONS = []
