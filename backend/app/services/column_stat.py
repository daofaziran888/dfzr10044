"""列统计领域服务：列级空值比例、去重基数与取值区间，统计版本绑定结构版本。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class ColumnStatService(BaseModuleService):
    MODULE = "column_stat"
    ENTITY = "列统计"
    OPERATION_TERM = "去重"
    LIST_FIELDS = ["统计编号", "所属湖表", "列名称", "空值比例", "去重基数", "最小值", "最大值", "统计版本"]
    REQUIRED_FIELDS = ["统计编号", "所属湖表", "列名称"]
    STATUS_ORDER = ["待计算", "已计算", "已失效", "计算失败"]
    ACTION_RULES = {"启动计算": "已计算", "确认有效": "已失效", "标记失效": "计算失败"}
    NEGATIVE_ACTIONS = []

    def compute_column_stats(self, lake_table: str, column_name: str) -> dict[str, Any]:
        """计算单列的空值比例、去重基数和取值范围。"""
        batches = lake_store.list_batches(lake_table)
        all_rows: list[dict[str, Any]] = []
        for br in batches:
            all_rows.extend(br.rows)

        values = [r.get(column_name) for r in all_rows if column_name in r]
        total = len(values)
        if total == 0:
            return {"lake_table": lake_table, "column": column_name, "total_count": 0,
                    "null_ratio": 0.0, "distinct_base": 0, "min_value": None, "max_value": None}

        null_count = sum(1 for v in values if v is None or v == "")
        null_ratio = null_count / total
        non_null = [v for v in values if v is not None and v != ""]
        distinct_base = len(set(non_null))

        min_val = min(non_null) if non_null else None
        max_val = max(non_null) if non_null else None

        return {
            "lake_table": lake_table,
            "column": column_name,
            "total_count": total,
            "null_count": null_count,
            "null_ratio": round(null_ratio, 4),
            "distinct_base": distinct_base,
            "min_value": min_val,
            "max_value": max_val,
        }

    def bind_version(self, column_name: str, schema_version: str) -> dict[str, Any]:
        """列统计绑定结构版本号。"""
        return {
            "column": column_name,
            "schema_version": schema_version,
            "binding_at": "now",
        }