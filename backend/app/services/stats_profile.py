"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class StatsProfileService(BaseModuleService):
    MODULE = "stats_profile"
    ENTITY = "统计画像"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["画像编号", "所属湖表", "统计粒度", "行数估算", "字节估算", "分区倾斜度", "采样比例", "统计时间"]
    REQUIRED_FIELDS = ["画像编号", "所属湖表", "统计粒度"]
    STATUS_ORDER = ["采样中", "已生成", "已过期", "生成失败"]
    ACTION_RULES = {"启动采样": "已生成", "确认生成": "已过期", "标记过期": "生成失败"}
    NEGATIVE_ACTIONS = []
