"""分区规划领域服务：基于统计画像推荐分区键和分区粒度。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class PartitionPlanService(BaseModuleService):
    MODULE = "partition_plan"
    ENTITY = "分区方案"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["方案编号", "所属湖表", "分区键", "分区粒度", "预期分区数", "单分区行数", "冷热判定", "最近评估"]
    REQUIRED_FIELDS = ["方案编号", "所属湖表", "分区键"]
    STATUS_ORDER = ["草稿", "评估中", "已采纳", "已驳回"]
    ACTION_RULES = {"提交评估": "评估中", "采纳方案": "已采纳", "驳回方案": "已驳回"}
    NEGATIVE_ACTIONS = ["驳回方案"]

    def recommend_partition(self, lake_table: str) -> dict[str, Any]:
        """基于湖表现有文件分布和统计画像推荐分区方案。"""
        files = lake_store.list_files(lake_table)
        partition_counts: dict[str, int] = {}
        partition_rows: dict[str, int] = {}
        for f in files:
            partition_counts[f.partition_key] = partition_counts.get(f.partition_key, 0) + 1
            partition_rows[f.partition_key] = partition_rows.get(f.partition_key, 0) + f.file_rows

        total_files = len(files)
        total_rows = sum(partition_rows.values())
        partition_count = len(partition_counts)
        avg_file_per_partition = total_files / partition_count if partition_count else 0
        avg_rows_per_partition = total_rows / partition_count if partition_count else 0

        # 如果一个小分区文件数过少（<3）说明不需要此分区粒度，建议升粗
        granularity_recommendation = "DAY"
        if avg_file_per_partition < 3 and partition_count > 10:
            granularity_recommendation = "MONTH"
        elif avg_file_per_partition > 20:
            granularity_recommendation = "HOUR"

        return {
            "lake_table": lake_table,
            "candidate_key": list(partition_counts.keys())[0] if partition_counts else "event_time",
            "recommended_granularity": granularity_recommendation,
            "estimated_partitions": partition_count,
            "avg_rows_per_partition": avg_rows_per_partition,
            "sample_time": time.time(),
        }

    def evaluate_partition_skew(self, lake_table: str) -> float:
        """评估分区倾斜度：最大分区占比。"""
        files = lake_store.list_files(lake_table)
        if not files:
            return 0.0
        partition_rows: dict[str, int] = {}
        for f in files:
            partition_rows[f.partition_key] = partition_rows.get(f.partition_key, 0) + f.file_rows
        total = sum(partition_rows.values())
        if total == 0:
            return 0.0
        return max(partition_rows.values()) / total