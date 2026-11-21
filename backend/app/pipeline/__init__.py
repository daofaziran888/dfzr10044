"""跨模块数据链路管线。

10条贯通链路覆盖湖表治理全生命周期，每条链路横跨3+模块：
- chain_register_evolve: 湖表登记→结构演进→分区规划
- chain_ingest_quality_quarantine: 入湖批次→质量规则→隔离区处置
- chain_watermark_batch_snapshot: 水位推进→批次写入→快照生成
- chain_write_commit_conflict: 写入作业→并发提交冲突→重试恢复
- chain_partition_evolve_coexist: 分区演化→双分区并存→切换完成
- chain_merge_recovery_compact: 归并中断→检查点恢复→压实确认
- chain_stats_column_compact: 统计画像→列统计→压实调度触发
- chain_snapshot_timetravel_expire: 快照管理→时间旅行读取→过期策略清理
- chain_tier_migration_watermark: 存储分层→冷热迁移→水位追踪
- chain_retention_audit_reclaim: 保留窗口→审计标记→到期回收
"""
from app.pipeline.chain_core import ChainResult, ChainContext, run_chain
from app.pipeline import chain_runner

__all__ = ["ChainResult", "ChainContext", "run_chain", "chain_runner"]