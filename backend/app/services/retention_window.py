"""保留窗口领域服务：保留粒度、保留周期、到期回收与审计标记。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class RetentionWindowService(BaseModuleService):
    MODULE = "retention_window"
    ENTITY = "保留窗口"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["窗口编号", "所属湖表", "保留粒度", "保留周期", "到期分区数", "受审计标记", "回收字节数", "最近回收"]
    REQUIRED_FIELDS = ["窗口编号", "所属湖表", "保留粒度"]
    STATUS_ORDER = ["生效中", "即将到期", "已回收", "已暂停"]
    ACTION_RULES = {"确认生效": "即将到期", "启动回收": "已回收", "暂停窗口": "已暂停"}
    NEGATIVE_ACTIONS = []

    def define_retention_window(self, lake_table: str, granularity: str,
                                retention_days: int, audit_tagged: bool = False) -> dict[str, Any]:
        """定义保留窗口：粒度、保留天数、是否受审计标记。"""
        return {
            "lake_table": lake_table,
            "granularity": granularity,
            "retention_days": retention_days,
            "audit_tagged": audit_tagged,
            "created_at": time.time(),
        }

    def identify_expired_partitions(self, lake_table: str,
                                    retention_days: int) -> list[str]:
        """识别到期分区。"""
        files = lake_store.list_files(lake_table)
        now = time.time()
        expired = []
        for f in files:
            age_days = (now - f.created_at) / 86400
            if age_days > retention_days:
                expired.append(f.file_id)
        return expired

    def reclaim_partitions(self, lake_table: str, file_ids: list[str]) -> dict[str, Any]:
        """回收到期分区文件。"""
        total_bytes = 0
        for fid in file_ids:
            pf = lake_store.get_file(lake_table, fid)
            if pf:
                total_bytes += pf.file_bytes
        removed = lake_store.remove_files(lake_table, file_ids)
        return {
            "lake_table": lake_table,
            "reclaimed_count": removed,
            "reclaimed_bytes": total_bytes,
            "reclaim_time": time.time(),
        }

    def check_audit_block(self, lake_table: str, audit_tagged: bool) -> dict[str, Any]:
        """检查审计标记是否阻塞回收。"""
        return {
            "lake_table": lake_table,
            "audit_tagged": audit_tagged,
            "block_reclaim": audit_tagged,
            "message": "受审计标记约束，回收前需先解除标记" if audit_tagged else "无审计阻塞",
        }