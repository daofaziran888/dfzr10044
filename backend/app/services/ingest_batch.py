"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class IngestBatchService(BaseModuleService):
    MODULE = "ingest_batch"
    ENTITY = "入湖批次"
    OPERATION_TERM = "采集"
    LIST_FIELDS = ["批次编号", "所属湖表", "来源系统", "批次行数", "采集窗口", "落湖快照", "完整校验值", "入湖时间"]
    REQUIRED_FIELDS = ["批次编号", "所属湖表", "来源系统"]
    STATUS_ORDER = ["待入湖", "入湖中", "已入湖", "入湖失败"]
    ACTION_RULES = {"启动入湖": "入湖中", "确认入湖": "已入湖", "标记失败": "入湖失败"}
    NEGATIVE_ACTIONS = []
