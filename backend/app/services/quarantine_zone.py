"""隔离区领域服务：存放违规批次行、待处置/回炉/留存管理。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class QuarantineZoneService(BaseModuleService):
    MODULE = "quarantine_zone"
    ENTITY = "隔离记录"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["隔离编号", "所属湖表", "来源批次", "违规规则", "违规行数", "隔离目录", "处置结论", "隔离时间"]
    REQUIRED_FIELDS = ["隔离编号", "所属湖表", "来源批次"]
    STATUS_ORDER = ["已隔离", "待处置", "已回炉", "已留存"]
    ACTION_RULES = {"提交处置": "待处置", "回炉重入": "已回炉", "永久留存": "已留存"}
    NEGATIVE_ACTIONS = []

    def isolate_violations(self, batch_id: str, rule_id: str, rule_name: str,
                           violation_rows: list[dict[str, Any]]) -> dict[str, Any]:
        """将违规数据行迁入隔离区。"""
        quarantined = lake_store.quarantine_rows(batch_id, rule_id, rule_name, violation_rows)
        return {
            "batch_id": batch_id,
            "rule_id": rule_id,
            "quarantine_count": len(quarantined),
            "status": "isolated",
        }

    def release_for_retry(self, batch_id: str) -> dict[str, Any]:
        """回炉重入：从隔离区取出数据行备重新入湖。"""
        rows = lake_store.release_quarantine(batch_id)
        return {
            "batch_id": batch_id,
            "released_count": len(rows),
            "released_rows": rows,
        }

    def dispose_permanently(self, batch_id: str) -> dict[str, Any]:
        """永久留存：标记处置结论为留存，不释放。"""
        saved = lake_store.list_quarantine(batch_id)
        return {
            "batch_id": batch_id,
            "disposition": "permanent_archive",
            "saved_count": len(saved),
        }

    def summary_by_lake_table(self, lake_table: str) -> dict[str, Any]:
        """汇总指定湖表的隔离区统计。"""
        all_quarantined = lake_store.list_quarantine()
        table_quarantined: dict[str, int] = {}
        for qr in all_quarantined:
            batch_id = qr.get("_quarantine_batch", "")
            br = lake_store.get_batch(batch_id)
            if br and br.lake_table == lake_table:
                rule = qr.get("_quarantine_rule", "unknown")
                table_quarantined[rule] = table_quarantined.get(rule, 0) + 1
        return {
            "lake_table": lake_table,
            "total_quarantined": sum(table_quarantined.values()),
            "by_rule": table_quarantined,
        }