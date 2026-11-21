"""入湖质量规则领域服务：校验列、阈值、违规处置与规则生命周期管理。"""
from __future__ import annotations

from typing import Any

from app.services.base import BaseModuleService
from app.store import store
from app.lake_store import lake_store


class QualityRuleService(BaseModuleService):
    MODULE = "quality_rule"
    ENTITY = "质量规则"
    OPERATION_TERM = "校验"
    LIST_FIELDS = ["规则编号", "所属湖表", "校验列", "校验类型", "阈值下限", "阈值上限", "违规处置", "命中批次"]
    REQUIRED_FIELDS = ["规则编号", "所属湖表", "校验列"]
    STATUS_ORDER = ["草稿", "已启用", "已抑制", "已废弃"]
    ACTION_RULES = {"启用规则": "已启用", "抑制规则": "已抑制", "废弃规则": "已废弃"}
    NEGATIVE_ACTIONS = []

    def apply_rules_to_batch(self, batch_id: str,
                             rules: list[dict[str, Any]]) -> dict[str, Any]:
        """对一个批次的全部行应用质量规则，返回违规行和通过行。"""
        br = lake_store.get_batch(batch_id)
        if br is None:
            return {"success": False, "error": "batch not found"}

        rows = br.rows
        violations: dict[int, list[str]] = {}
        for i, row in enumerate(rows):
            row_violations = []
            for rule in rules:
                col = rule.get("校验列", "")
                rule_type = rule.get("校验类型", "")
                lo = self._parse_limit(rule.get("阈值下限"))
                hi = self._parse_limit(rule.get("阈值上限"))
                if col not in row:
                    continue
                val = row[col]
                if rule_type == "NOT_NULL" and (val is None or str(val).strip() == ""):
                    row_violations.append(rule.get("规则编号", ""))
                elif rule_type == "UNIQUE":
                    pass
                elif rule_type == "RANGE" and (val is not None and str(val).strip() != ""):
                    try:
                        num_val = float(str(val))
                        if (lo is not None and num_val < lo) or (hi is not None and num_val > hi):
                            row_violations.append(rule.get("规则编号", ""))
                    except (ValueError, TypeError):
                        row_violations.append(rule.get("规则编号", ""))
            if row_violations:
                violations[i] = row_violations

        clean_rows = [rows[i] for i in range(len(rows)) if i not in violations]
        violation_rows = [rows[i] for i in violations]
        return {
            "batch_id": batch_id,
            "total_rows": len(rows),
            "clean_rows": len(clean_rows),
            "violation_rows": len(violation_rows),
            "violations_by_row": {str(k): v for k, v in violations.items()},
            "violation_data": violation_rows,
            "clean_data": clean_rows,
        }

    def _parse_limit(self, value: Any) -> float | None:
        if value is None or str(value).strip() == "":
            return None
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return None