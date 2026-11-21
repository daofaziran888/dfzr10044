"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class LakeCatalogService(BaseModuleService):
    MODULE = "lake_catalog"
    ENTITY = "湖表条目"
    OPERATION_TERM = "入湖"
    LIST_FIELDS = ["表编号", "表名全称", "所属库域", "表格式", "存储路径", "负责人标识", "登记时间", "当前版本"]
    REQUIRED_FIELDS = ["表编号", "表名全称", "所属库域"]
    STATUS_ORDER = ["待登记", "已登记", "已冻结", "已下线"]
    ACTION_RULES = {"确认登记": "已登记", "冻结条目": "已冻结", "下线条目": "已下线"}
    NEGATIVE_ACTIONS = ["下线条目"]
