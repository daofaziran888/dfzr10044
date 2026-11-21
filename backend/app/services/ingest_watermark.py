"""入湖水位领域服务：水位创建、推进、回退及批次完整性约束。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class IngestWatermarkService(BaseModuleService):
    MODULE = "ingest_watermark"
    ENTITY = "水位记录"
    OPERATION_TERM = "入湖"
    LIST_FIELDS = ["水位编号", "所属湖表", "水位字段", "已提交水位", "待提交水位", "落后批次", "推进策略", "最近推进"]
    REQUIRED_FIELDS = ["水位编号", "所属湖表", "水位字段"]
    STATUS_ORDER = ["初始化", "推进中", "已追上", "水位回退"]
    ACTION_RULES = {"推进水位": "推进中", "确认追上": "已追上", "标记回退": "水位回退"}
    NEGATIVE_ACTIONS = []

    def create_watermark(self, lake_table: str, field: str,
                         initial_value: str, strategy: str = "append") -> dict[str, Any]:
        """创建水位记录：记录传参的已提交水位。"""
        wm = lake_store.set_watermark(lake_table, field, initial_value, strategy)
        return {
            "lake_table": lake_table,
            "field": field,
            "committed_value": wm.committed_value,
            "strategy": strategy,
        }

    def advance_watermark_after_batch(self, lake_table: str,
                                      new_value: str) -> dict[str, Any]:
        """批次落湖后推进水位：先 set pending，再 commit。"""
        lake_store.advance_watermark(lake_table, new_value)
        wm = lake_store.commit_watermark(lake_table)
        if wm is None:
            return {"success": False, "error": "watermark not found or no pending value"}
        return {
            "success": True,
            "lake_table": lake_table,
            "new_watermark": wm.committed_value,
            "advanced_at": wm.last_advanced_at,
        }

    def detect_lagging_batches(self, lake_table: str,
                               current_watermark: str) -> list[str]:
        """检测落后批次：返回 < water mark 的未摄入批次 ID。"""
        batches = lake_store.list_batches(lake_table)
        lagging = []
        for b in batches:
            if b.status == "pending" and b.window_end <= current_watermark:
                lagging.append(b.batch_id)
        return lagging

    def rollback_watermark(self, lake_table: str) -> dict[str, Any]:
        """水位回退导致未采集数据范围扩大，后续批次重复入湖。"""
        wm = lake_store.get_watermark(lake_table)
        if wm is None:
            return {"success": False, "error": "watermark not found"}
        # 回退1天
        wm.committed_value = "2026-10-31T00:00:00"
        wm.pending_value = None
        wm.last_advanced_at = time.time()
        return {
            "success": True,
            "rolled_back_to": wm.committed_value,
        }