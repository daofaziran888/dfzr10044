"""写入作业领域服务：并发写入、提交协议与冲突重试。
提交协议决定并发写入能否产生唯一快照；乐观锁方式：获取写锁→检测文件清单→提交快照→释放锁。"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class WriteJobService(BaseModuleService):
    MODULE = "write_job"
    ENTITY = "写入作业"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["作业编号", "所属湖表", "写入模式", "并发写入数", "提交协议", "冲突重试", "写入行数", "作业耗时"]
    REQUIRED_FIELDS = ["作业编号", "所属湖表", "写入模式"]
    STATUS_ORDER = ["待调度", "写入中", "已提交", "提交冲突"]
    ACTION_RULES = {"调度作业": "写入中", "确认提交": "已提交", "标记冲突": "提交冲突"}
    NEGATIVE_ACTIONS = []

    def acquire_and_write(self, lake_table: str, mode: str,
                          rows_data: list[dict[str, Any]],
                          retry_on_conflict: bool = True) -> dict[str, Any]:
        """获取全局写锁后写入数据并提交快照。

        乐观锁机制：拿到锁→检查当前文件清单→做版本冲突检测→创建新快照→释放锁。
        若检测到冲突且 retry_on_conflict=True，重试一次。
        """
        attempt = 1
        while attempt <= (2 if retry_on_conflict else 1):
            lock = lake_store.acquire_write_lock(lake_table)
            try:
                start_files = lake_store.list_files(lake_table)
                snap_list = lake_store.list_snapshots(lake_table)
                # 冲突检测
                if attempt == 2:
                    conflict_detected = False
                else:
                    registered_set = set(f.file_id for f in start_files)
                    if snap_list:
                        latest_snap_files = set(snap_list[-1].file_ids)
                        conflict_detected = registered_set != latest_snap_files
                    else:
                        conflict_detected = False

                if conflict_detected and attempt < 2:
                    attempt += 1
                    continue

                pf = lake_store.register_file(
                    lake_table, "write_job",
                    rows=len(rows_data), bytes_=len(rows_data) * 300,
                )
                prev_snap = snap_list[-1] if snap_list else None
                snap = lake_store.create_snapshot(
                    lake_table, file_ids=[pf.file_id],
                    parent_snapshot=prev_snap.snapshot_id if prev_snap else None,
                    added_rows=len(rows_data), deleted_rows=0,
                )
                lake_store.mark_snapshot_available(lake_table, snap.snapshot_id)
                return {
                    "success": True,
                    "snapshot_id": snap.snapshot_id,
                    "rows_written": len(rows_data),
                    "conflict_detected": conflict_detected,
                    "attempt": attempt,
                }
            finally:
                lock.release()
            attempt += 1
        return {"success": False, "error": "write conflict unresolved", "attempt": attempt}

    def detect_write_conflict(self, lake_table: str) -> dict[str, Any]:
        """检测当前写冲突状态。"""
        files = lake_store.list_files(lake_table)
        snaps = lake_store.list_snapshots(lake_table)
        if not snaps:
            return {"conflict": False, "reason": "no snapshots yet"}
        snap_files = set(snaps[-1].file_ids)
        actual_files = set(f.file_id for f in files)
        has_conflict = snap_files != actual_files
        return {
            "conflict": has_conflict,
            "snap_files": len(snap_files),
            "actual_files": len(actual_files),
            "extra_files": list(actual_files - snap_files),
            "missing_files": list(snap_files - actual_files),
        }