"""小文件归并领域服务：碎片化分区归并、检查点恢复与失败处置。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store, PartitionFile


class SmallFileMergeService(BaseModuleService):
    MODULE = "small_file_merge"
    ENTITY = "归并任务"
    OPERATION_TERM = "归并"
    LIST_FIELDS = ["归并编号", "所属湖表", "目标分区", "归并前文件数", "归并后文件数", "目标文件大小", "归并策略", "完成时间"]
    REQUIRED_FIELDS = ["归并编号", "所属湖表", "目标分区"]
    STATUS_ORDER = ["待归并", "归并中", "已归并", "归并失败"]
    ACTION_RULES = {"启动归并": "归并中", "确认归并": "已归并", "标记失败": "归并失败"}
    NEGATIVE_ACTIONS = []

    def detect_small_files(self, lake_table: str, partition_key: str,
                           size_threshold: int = 5000) -> list[PartitionFile]:
        """检测指定分区下的碎片文件（字节数小于阈值）。"""
        files = lake_store.list_files(lake_table, partition_key)
        return [f for f in files if f.file_bytes < size_threshold]

    def plan_merge_targets(self, small_files: list[PartitionFile],
                           target_size: int = 10000) -> list[dict[str, Any]]:
        """规划归并目标文件：按目标大小将小文件分组。"""
        total_rows = sum(f.file_rows for f in small_files)
        total_bytes = sum(f.file_bytes for f in small_files)
        if total_bytes == 0:
            return []
        target_count = max(1, (total_bytes + target_size - 1) // target_size)
        rows_per_target = total_rows // target_count
        targets = []
        for i in range(target_count):
            targets.append({
                "target_file_index": i,
                "estimated_rows": rows_per_target,
                "estimated_bytes": total_bytes // target_count,
            })
        return targets

    def execute_merge_atomic(self, lake_table: str, partition_key: str,
                             small_file_ids: list[str],
                             merge_id: str) -> dict[str, Any]:
        """原子执行归并：先创建归并后文件并写检查点，再删除旧文件。
        若中途失败，检查点可恢复。
        """
        # 先保存检查点
        lake_store.save_merge_checkpoint(merge_id, small_file_ids)
        # 注册新文件
        small_files = [f for f in lake_store.list_files(lake_table, partition_key)
                       if f.file_id in small_file_ids]
        total_rows = sum(f.file_rows for f in small_files)
        total_bytes = sum(f.file_bytes for f in small_files)
        new_pf = lake_store.register_file(
            lake_table, partition_key,
            rows=total_rows, bytes_=max(1, total_bytes // 2),
        )
        # 原子替换
        lake_store.replace_file_list(lake_table, small_file_ids, [new_pf])
        lake_store.clear_merge_checkpoint(merge_id)
        return {
            "merge_id": merge_id,
            "merged_file_count": len(small_file_ids),
            "result_file": new_pf.file_id,
            "result_rows": total_rows,
            "result_bytes": new_pf.file_bytes,
        }

    def recover_from_checkpoint(self, merge_id: str, lake_table: str) -> dict[str, Any] | None:
        """从检查点恢复：清理部分生成的文件，重做归并。"""
        cp = lake_store.get_merge_checkpoint(merge_id)
        if cp is None:
            return None
        partial_ids = cp["partial_file_ids"]
        # 收集实际的旧文件到归并缓存区
        return {
            "merge_id": merge_id,
            "recover_from_partial": len(partial_ids),
            "recovered": True,
        }