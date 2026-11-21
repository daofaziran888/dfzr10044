"""链路执行引擎：ChainContext 承载跨模块共享数据上下文，run_chain 协调多模块步骤。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ChainContext:
    """跨模块链路共享的数据上下文。

    每个步骤将工艺中间产物写入 context，后续步骤读取继续处理。
    校验失败时 error_skip 控制跳过后继步骤。
    """
    lake_table: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    error_skip: bool = False
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChainResult:
    """链路执行结果：记录每一步的成功/失败及其产物。"""
    success: bool
    lake_table: str
    chain_name: str
    steps: list[dict[str, Any]]
    final_output: dict[str, Any]
    error_count: int = 0


StepFunc = Callable[[ChainContext], ChainContext]


def run_chain(name: str, lake_table: str, steps: list[tuple[str, StepFunc]]) -> ChainResult:
    """按顺序执行链路步骤。

    每一步都返回更新后的 ChainContext。
    如果 context.error_skip 被某步骤设为 True，跳过后续步骤。
    """
    ctx = ChainContext(lake_table=lake_table)
    result_steps: list[dict[str, Any]] = []
    error_count = 0

    for step_name, step_fn in steps:
        if ctx.error_skip:
            result_steps.append({
                "step": step_name,
                "status": "skipped",
                "output_keys": [],
            })
            continue
        try:
            ctx = step_fn(ctx)
            result_steps.append({
                "step": step_name,
                "status": "ok",
                "output_keys": list(ctx.output.keys()),
            })
        except Exception as exc:
            error_count += 1
            result_steps.append({
                "step": step_name,
                "status": "error",
                "error": str(exc),
                "output_keys": list(ctx.output.keys()),
            })
            ctx.error_skip = True

    return ChainResult(
        success=error_count == 0 and not ctx.error_skip,
        lake_table=lake_table,
        chain_name=name,
        steps=result_steps,
        final_output=dict(ctx.output),
        error_count=error_count,
    )