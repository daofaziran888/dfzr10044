"""压实作业领域服务：基于触发条件的湖表分区压实，保留快照可读性。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class CompactJobService(BaseModuleService):
    MODULE = "compact_job"
    ENTITY = "压实作业"
    OPERATION_TERM = "读取"
    LIST_FIELDS = ["压实编号", "所属湖表", "触发条件", "目标分区", "读取文件数", "输出文件数", "占用资源额度", "压实耗时"]
    REQUIRED_FIELDS = ["压实编号", "所属湖表", "触发条件"]
    STATUS_ORDER = ["待触发", "压实中", "已完成", "压实中断"]
    ACTION_RULES = {"触发压实": "压实中", "确认完成": "已完成", "标记中断": "压实中断"}
    NEGATIVE_ACTIONS = []

    def evaluate_compact_trigger(self, lake_table: str) -> dict[str, Any]:
        """评估压实触发条件：按文件数量与总字节数判定。"""
        files = lake_store.list_files(lake_table)
        total_files = len(files)
        total_bytes = sum(f.file_bytes for f in files)
        small_files = [f for f in files if f.file_bytes < 3000]
        triggers = {
            "文件过多": total_files > 20,
            "碎片文件超过阈值": len(small_files) > 5,
            "单分区文件密度高": any(
                sum(1 for ff in files if ff.partition_key == f.partition_key) > 8
                for f in files
            ),
        }
        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "small_file_count": len(small_files),
            "trigger_conditions": triggers,
            "should_trigger": any(triggers.values()),
        }

    def execute_compact(self, lake_table: str, partition_key: str) -> dict[str, Any]:
        """执行压实：读取指定分区的全部文件，合并为一个输出文件。"""
        start_time = time.time()
        files = lake_store.list_files(lake_table, partition_key)
        read_count = len(files)
        total_rows = sum(f.file_rows for f in files)
        # 压缩后体积降低
        compact_pf = lake_store.register_file(
            lake_table, partition_key,
            rows=total_rows, bytes_=max(1, sum(f.file_bytes for f in files) // 2),
        )
        # 原子替换
        old_ids = [f.file_id for f in files]
        lake_store.replace_file_list(lake_table, old_ids, [compact_pf])
        elapsed = time.time() - start_time
        return {
            "lake_table": lake_table,
            "partition": partition_key,
            "read_files": read_count,
            "output_files": 1,
            "total_rows": total_rows,
            "elapsed": elapsed,
            "compact_success": True,
        }