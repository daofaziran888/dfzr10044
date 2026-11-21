"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class QualityRuleService(BaseModuleService):
    MODULE = "quality_rule"
    ENTITY = "质量规则"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "所属湖表", "校验列", "校验类型", "阈值下限", "阈值上限", "违规处置", "命中批次"]
    REQUIRED_FIELDS = ["规则编号", "所属湖表", "校验列"]
    STATUS_ORDER = ["草稿", "已启用", "已抑制", "已废弃"]
    ACTION_RULES = {"启用规则": "已启用", "抑制规则": "已抑制", "废弃规则": "已废弃"}
    NEGATIVE_ACTIONS = []
