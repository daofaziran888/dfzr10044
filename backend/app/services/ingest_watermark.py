"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class IngestWatermarkService(BaseModuleService):
    MODULE = "ingest_watermark"
    ENTITY = "水位记录"
    OPERATION_TERM = "入湖"
    LIST_FIELDS = ["水位编号", "所属湖表", "水位字段", "已提交水位", "待提交水位", "落后批次", "推进策略", "最近推进"]
    REQUIRED_FIELDS = ["水位编号", "所属湖表", "水位字段"]
    STATUS_ORDER = ["初始化", "推进中", "已追上", "水位回退"]
    ACTION_RULES = {"推进水位": "推进中", "确认追上": "已追上", "标记回退": "水位回退"}
    NEGATIVE_ACTIONS = []
