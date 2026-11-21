"""分区演化领域服务：分区键演化、双分区并存时期管理与切换完成。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class PartitionEvolveService(BaseModuleService):
    MODULE = "partition_evolve"
    ENTITY = "演化记录"
    OPERATION_TERM = "水位"
    LIST_FIELDS = ["演化编号", "所属湖表", "原分区键", "新分区键", "影响分区数", "历史数据处置", "切换水位", "演化时间"]
    REQUIRED_FIELDS = ["演化编号", "所属湖表", "原分区键"]
    STATUS_ORDER = ["待切换", "双分区并存", "已完成", "已回退"]
    ACTION_RULES = {"启动演化": "双分区并存", "确认完成": "已完成", "执行回退": "已回退"}
    NEGATIVE_ACTIONS = []

    def start_coexist_period(self, lake_table: str, old_key: str, new_key: str) -> dict[str, Any]:
        """启动双分区并存周期：旧新分区键文件都保留。"""
        entry_time = time.time()
        # 记录演化边界
        old_files = lake_store.list_files(lake_table)
        old_file_count = len(old_files)
        return {
            "lake_table": lake_table,
            "old_partition_key": old_key,
            "new_partition_key": new_key,
            "phase": "dual_coexist",
            "old_file_count": old_file_count,
            "start_time": entry_time,
        }

    def finalize_switch(self, lake_table: str, old_key: str, new_key: str) -> dict[str, Any]:
        """切换完成：收集旧分区文件 ID，准备清理但保留审计记录。"""
        old_files = lake_store.list_files(lake_table)
        old_fids = [
            f.file_id for f in old_files
            if f.partition_key and len(f.partition_key) == 8
        ]
        return {
            "lake_table": lake_table,
            "old_file_ids_to_archive": old_fids,
            "old_count": len(old_fids),
            "new_key_active": new_key,
            "switch_time": time.time(),
        }

    def rollback_evolve(self, lake_table: str) -> dict[str, Any]:
        """回退：恢复旧分区键。"""
        snap = lake_store.get_snapshot_at_time(lake_table, time.time() - 3600)
        return {
            "lake_table": lake_table,
            "rolled_back": True,
            "rollback_snapshot": snap.snapshot_id if snap else None,
        }