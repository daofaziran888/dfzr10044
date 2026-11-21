"""统计画像领域服务：采样汇总湖表行数、字节与分区倾斜度，供分区规划和压实触发共同引用。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class StatsProfileService(BaseModuleService):
    MODULE = "stats_profile"
    ENTITY = "统计画像"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["画像编号", "所属湖表", "统计粒度", "行数估算", "字节估算", "分区倾斜度", "采样比例", "统计时间"]
    REQUIRED_FIELDS = ["画像编号", "所属湖表", "统计粒度"]
    STATUS_ORDER = ["采样中", "已生成", "已过期", "生成失败"]
    ACTION_RULES = {"启动采样": "已生成", "确认生成": "已过期", "标记过期": "生成失败"}
    NEGATIVE_ACTIONS = []

    def sample_table_stats(self, lake_table: str, granularity: str = "TABLE") -> dict[str, Any]:
        """按粒度采样湖表统计信息。"""
        files = lake_store.list_files(lake_table)
        snaps = lake_store.list_snapshots(lake_table)
        total_rows = sum(f.file_rows for f in files)
        total_bytes = sum(f.file_bytes for f in files)

        # 按分区计数找到最大分区占比
        partition_rows: dict[str, int] = {}
        for f in files:
            partition_rows[f.partition_key] = partition_rows.get(f.partition_key, 0) + f.file_rows
        max_partition_share = (max(partition_rows.values()) / total_rows) if total_rows else 0

        return {
            "lake_table": lake_table,
            "granularity": granularity,
            "total_rows": total_rows,
            "total_bytes": total_bytes,
            "partition_count": len(partition_rows),
            "max_partition_skew": round(max_partition_share, 4),
            "available_snapshots": sum(1 for s in snaps if s.status == "available"),
            "sample_time": time.time(),
        }

    def profile_skew_distribution(self, lake_table: str) -> list[dict[str, Any]]:
        """按分区输出倾斜度分布。"""
        files = lake_store.list_files(lake_table)
        partition_rows: dict[str, int] = {}
        partition_bytes: dict[str, int] = {}
        for f in files:
            partition_rows[f.partition_key] = partition_rows.get(f.partition_key, 0) + f.file_rows
            partition_bytes[f.partition_key] = partition_bytes.get(f.partition_key, 0) + f.file_bytes
        total_rows = sum(partition_rows.values()) or 1
        return [
            {
                "partition": pk,
                "rows": partition_rows[pk],
                "bytes": partition_bytes[pk],
                "skew_ratio": round(partition_rows[pk] / total_rows, 4),
            }
            for pk in sorted(partition_rows.keys())
        ]