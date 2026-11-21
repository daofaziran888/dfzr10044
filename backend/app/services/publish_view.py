"""__NAME__领域服务：字段、状态和动作来自业务配置，数据处理骨架由基类复用。"""
from __future__ import annotations

from app.services.base import BaseModuleService


class PublishViewService(BaseModuleService):
    MODULE = "publish_view"
    ENTITY = "消费视图"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["视图编号", "所属湖表", "视图定义", "绑定快照", "可见列", "刷新方式", "下游消费方", "最近刷新"]
    REQUIRED_FIELDS = ["视图编号", "所属湖表", "视图定义"]
    STATUS_ORDER = ["草稿", "已发布", "刷新中", "已撤回"]
    ACTION_RULES = {"发布视图": "已发布", "触发刷新": "刷新中", "撤回视图": "已撤回"}
    NEGATIVE_ACTIONS = []
