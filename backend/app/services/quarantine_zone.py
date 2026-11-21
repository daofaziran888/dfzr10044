"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QuarantineZoneService(BaseModuleService):
    MODULE = "quarantine_zone"
    ENTITY = "隔离记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["隔离编号", "所属湖表", "来源批次", "违规规则", "违规行数", "隔离目录", "处置结论", "隔离时间"]
    REQUIRED_FIELDS = ["隔离编号", "所属湖表", "来源批次"]
    STATUS_ORDER = ["已隔离", "待处置", "已回炉", "已留存"]
    ACTION_RULES = {"提交处置": "待处置", "回炉重入": "已回炉", "永久留存": "已留存"}
    NEGATIVE_ACTIONS = []
