"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class TableSchemaService(BaseModuleService):
    MODULE = "table_schema"
    ENTITY = "结构版本"
    OPERATION_TERM = "读取"
    LIST_FIELDS = ["版本编号", "所属湖表", "列清单", "类型声明", "兼容判定", "父版本号", "变更原因", "生效时间"]
    REQUIRED_FIELDS = ["版本编号", "所属湖表", "列清单"]
    STATUS_ORDER = ["草稿", "待判定", "已生效", "已作废"]
    ACTION_RULES = {"提交判定": "待判定", "生效版本": "已生效", "作废版本": "已作废"}
    NEGATIVE_ACTIONS = ["作废版本"]
