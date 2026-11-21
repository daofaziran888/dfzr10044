"""存储分层领域服务：维护热层/冷层判定、迁移窗口与压缩算法。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class StorageTierService(BaseModuleService):
    MODULE = "storage_tier"
    ENTITY = "分层规则"
    OPERATION_TERM = "存储"
    LIST_FIELDS = ["分层编号", "所属湖表", "热层判定", "冷层判定", "迁移窗口", "压缩算法", "迁移字节数", "最近迁移"]
    REQUIRED_FIELDS = ["分层编号", "所属湖表", "热层判定"]
    STATUS_ORDER = ["草稿", "已生效", "迁移中", "已暂停"]
    ACTION_RULES = {"启效分层": "已生效", "启动迁移": "迁移中", "暂停分层": "已暂停"}
    NEGATIVE_ACTIONS = []

    def classify_to_tier(self, lake_table: str, hot_days: int = 7) -> dict[str, Any]:
        """按时间窗口区分热层/冷层：创建时间超过 hot_days 的分区为冷层。"""
        files = lake_store.list_files(lake_table)
        now = time.time()
        hot_file_ids: list[str] = []
        cold_file_ids: list[str] = []
        for f in files:
            age_days = (now - f.created_at) / 86400
            if age_days <= hot_days:
                hot_file_ids.append(f.file_id)
            else:
                cold_file_ids.append(f.file_id)
        return {
            "lake_table": lake_table,
            "hot_file_count": len(hot_file_ids),
            "cold_file_count": len(cold_file_ids),
            "hot_bytes": sum(
                (lake_store.get_file(lake_table, fid) or PartitionFile("", "", "", 0, 0, "", 0)).file_bytes
                if lake_store.get_file(lake_table, fid) else 0
                for fid in hot_file_ids
            ),
            "cold_bytes": sum(
                (lake_store.get_file(lake_table, fid) or PartitionFile("", "", "", 0, 0, "", 0)).file_bytes
                if lake_store.get_file(lake_table, fid) else 0
                for fid in cold_file_ids
            ),
        }

    def migrate_cold_files(self, lake_table: str, compression: str = "SNAPPY") -> dict[str, Any]:
        """迁移冷层文件到压缩存储。"""
        files = lake_store.list_files(lake_table)
        migrated_fids = []
        migrated_bytes = 0
        for f in files:
            original_bytes = f.file_bytes
            # 冷层压缩体积降 60%
            f.file_bytes = max(1, int(original_bytes * 0.4))
            migrated_bytes += original_bytes - f.file_bytes
            migrated_fids.append(f.file_id)
        return {
            "lake_table": lake_table,
            "compression": compression,
            "migrated_file_count": len(migrated_fids),
            "bytes_saved": migrated_bytes,
        }

from app.lake_store import PartitionFile