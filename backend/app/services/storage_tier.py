"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class StorageTierService(BaseModuleService):
    MODULE = "storage_tier"
    ENTITY = "分层规则"
    OPERATION_TERM = "存储"
    LIST_FIELDS = ["分层编号", "所属湖表", "热层判定", "冷层判定", "迁移窗口", "压缩算法", "迁移字节数", "最近迁移"]
    REQUIRED_FIELDS = ["分层编号", "所属湖表", "热层判定"]
    STATUS_ORDER = ["草稿", "已生效", "迁移中", "已暂停"]
    ACTION_RULES = {"启效分层": "已生效", "启动迁移": "迁移中", "暂停分层": "已暂停"}
    NEGATIVE_ACTIONS = []
