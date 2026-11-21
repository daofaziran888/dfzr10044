"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class WriteJobService(BaseModuleService):
    MODULE = "write_job"
    ENTITY = "写入作业"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["作业编号", "所属湖表", "写入模式", "并发写入数", "提交协议", "冲突重试", "写入行数", "作业耗时"]
    REQUIRED_FIELDS = ["作业编号", "所属湖表", "写入模式"]
    STATUS_ORDER = ["待调度", "写入中", "已提交", "提交冲突"]
    ACTION_RULES = {"调度作业": "写入中", "确认提交": "已提交", "标记冲突": "提交冲突"}
    NEGATIVE_ACTIONS = []
