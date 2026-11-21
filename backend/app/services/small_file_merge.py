"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class SmallFileMergeService(BaseModuleService):
    MODULE = "small_file_merge"
    ENTITY = "归并任务"
    OPERATION_TERM = "归并"
    LIST_FIELDS = ["归并编号", "所属湖表", "目标分区", "归并前文件数", "归并后文件数", "目标文件大小", "归并策略", "完成时间"]
    REQUIRED_FIELDS = ["归并编号", "所属湖表", "目标分区"]
    STATUS_ORDER = ["待归并", "归并中", "已归并", "归并失败"]
    ACTION_RULES = {"启动归并": "归并中", "确认归并": "已归并", "标记失败": "归并失败"}
    NEGATIVE_ACTIONS = []
