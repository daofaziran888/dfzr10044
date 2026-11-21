"""资源额度计量领域服务：计量写入、压实与迁移资源用量，超额限流。"""
from __future__ import annotations

import time
from typing import Any

from app.services.base import BaseModuleService
from app.store import store


class QuotaMeterService(BaseModuleService):
    MODULE = "quota_meter"
    ENTITY = "额度读数"
    OPERATION_TERM = "写入"
    LIST_FIELDS = ["读数编号", "所属湖表", "额度类型", "已用额度", "额度上限", "计量窗口", "超额处置", "计量时间"]
    REQUIRED_FIELDS = ["读数编号", "所属湖表", "额度类型"]
    STATUS_ORDER = ["计量中", "已结算", "超额告警", "已冻结"]
    ACTION_RULES = {"确认结算": "已结算", "标记超额": "超额告警", "冻结额度": "已冻结"}
    NEGATIVE_ACTIONS = []

    def meter_resource(self, lake_table: str, quota_type: str, used_amount: float,
                       quota_limit: float, window: str) -> dict[str, Any]:
        """计量资源额度用量并判定是否超额。"""
        over_quota = used_amount > quota_limit
        status = "超额告警" if over_quota else "已结算"
        disposition = "限流" if over_quota else "None"
        return {
            "lake_table": lake_table,
            "quota_type": quota_type,
            "used_amount": used_amount,
            "quota_limit": quota_limit,
            "usage_ratio": round(used_amount / max(1, quota_limit), 4),
            "over_quota": over_quota,
            "status": status,
            "disposition": disposition,
            "window": window,
            "meter_time": time.time(),
        }

    def throttle_if_over_quota(self, lake_table: str, requested_amount: float) -> dict[str, Any]:
        """超额处置：超额时返回限流建议而非直接拒绝。"""
        return {
            "lake_table": lake_table,
            "requested": requested_amount,
            "throttled": requested_amount > 100000,
            "suggestion": "请求超额，建议缩小批次重试" if requested_amount > 100000 else "通过",
        }