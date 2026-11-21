"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class ColumnStatService(BaseModuleService):
    MODULE = "column_stat"
    ENTITY = "列统计"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["统计编号", "所属湖表", "列名称", "空值比例", "去重基数", "最小值", "最大值", "统计版本"]
    REQUIRED_FIELDS = ["统计编号", "所属湖表", "列名称"]
    STATUS_ORDER = ["待计算", "已计算", "已失效", "计算失败"]
    ACTION_RULES = {"启动计算": "已计算", "确认有效": "已失效", "标记失效": "计算失败"}
    NEGATIVE_ACTIONS = []
