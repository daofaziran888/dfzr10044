"""结构演进领域服务：列结构的版本化记录与兼容性判定。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class TableSchemaService(BaseModuleService):
    MODULE = "table_schema"
    ENTITY = "结构版本"
    OPERATION_TERM = "读取"
    LIST_FIELDS = ["版本编号", "所属湖表", "列清单", "类型声明", "兼容判定", "父版本号", "变更原因", "生效时间"]
    REQUIRED_FIELDS = ["版本编号", "所属湖表", "列清单"]
    STATUS_ORDER = ["草稿", "待判定", "已生效", "已作废"]
    ACTION_RULES = {"提交判定": "待判定", "生效版本": "已生效", "作废版本": "已作废"}
    NEGATIVE_ACTIONS = ["作废版本"]

    def judge_compatibility(self, current_columns: list[dict[str, Any]],
                            parent_columns: list[dict[str, Any]]) -> str:
        """判定列结构演进的兼容性。

        规则：
        - 新增可空列→BACKWARD_COMPATIBLE
        - 删除列→BREAKING
        - 修改列类型→BREAKING
        - 无变化→SAME
        """
        if not parent_columns:
            return "INITIAL_VERSION"
        current_map = {c["name"]: c for c in current_columns}
        parent_map = {c["name"]: c for c in parent_columns}
        for name, col in current_map.items():
            if name not in parent_map:
                if col.get("nullable", True):
                    continue
                return "BREAKING_NON_NULLABLE_NEW"
        for name in parent_map:
            if name not in current_map:
                return "BREAKING_COLUMN_DROPPED"
        for name, col in current_map.items():
            if name in parent_map:
                if col.get("type") != parent_map[name].get("type"):
                    return "BREAKING_TYPE_CHANGED"
        added_cols = set(current_map) - set(parent_map)
        if added_cols:
            return "BACKWARD_COMPATIBLE"
        return "SAME"

    def get_version_chain(self, lake_table: str) -> list[dict[str, Any]]:
        """获取指定湖表的版本链（按父版本号回溯）。"""
        rows = store.rows(self.MODULE)
        chain = [
            r for r in rows
            if str(r.get("所属湖表", "")) == lake_table
        ]
        chain.sort(key=lambda r: str(r.get("版本编号", "")))
        return chain