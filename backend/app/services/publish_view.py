"""消费视图领域服务：发布、刷新、撤回面向下游的视图，绑定快照与结构版本。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class PublishViewService(BaseModuleService):
    MODULE = "publish_view"
    ENTITY = "消费视图"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["视图编号", "所属湖表", "视图定义", "绑定快照", "可见列", "刷新方式", "下游消费方", "最近刷新"]
    REQUIRED_FIELDS = ["视图编号", "所属湖表", "视图定义"]
    STATUS_ORDER = ["草稿", "已发布", "刷新中", "已撤回"]
    ACTION_RULES = {"发布视图": "已发布", "触发刷新": "刷新中", "撤回视图": "已撤回"}
    NEGATIVE_ACTIONS = []

    def publish_view(self, lake_table: str, view_definition: str,
                     visible_columns: list[str], consumer: str) -> dict[str, Any]:
        """发布消费视图：绑定最新可用快照与可见列。"""
        snaps = lake_store.list_snapshots(lake_table)
        available = [s for s in snaps if s.status == "available"]
        latest_snap = available[-1] if available else None
        return {
            "lake_table": lake_table,
            "view_definition": view_definition,
            "bound_snapshot": latest_snap.snapshot_id if latest_snap else None,
            "visible_columns": visible_columns,
            "consumer": consumer,
            "published_at": time.time(),
        }

    def refresh_view(self, lake_table: str, view_snapshot: str) -> dict[str, Any]:
        """触发视图刷新：更新绑定快照到最新。"""
        snaps = lake_store.list_snapshots(lake_table)
        available = [s for s in snaps if s.status == "available"]
        if not available:
            return {"success": False, "error": "no available snapshot"}
        latest = available[-1]
        return {
            "success": True,
            "previous_snapshot": view_snapshot,
            "refreshed_snapshot": latest.snapshot_id,
            "refresh_time": time.time(),
        }

    def revoke_view(self, lake_table: str, consumer: str) -> dict[str, Any]:
        """撤回视图：撤销下游消费方对视图的访问授权。"""
        return {
            "lake_table": lake_table,
            "consumer": consumer,
            "revoked": True,
            "revoke_time": time.time(),
        }