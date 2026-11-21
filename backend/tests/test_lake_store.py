"""测试湖表存储引擎核心能力：文件注册、快照链、水位、批次、隔离区、并发锁。"""
from __future__ import annotations

import time
import uuid

import pytest

from app.lake_store import LakeStore, PartitionFile, WriteLock


@pytest.fixture
def lake_store_fixture() -> LakeStore:
    return LakeStore()


class TestFileRegistry:
    def test_register_and_list_files(self, lake_store_fixture):
        store = lake_store_fixture
        pf = store.register_file("tbl_test", "20261101", rows=100, bytes_=25600)
        assert pf.lake_table == "tbl_test"
        assert pf.partition_key == "20261101"
        assert pf.file_rows == 100

        files = store.list_files("tbl_test")
        assert len(files) == 1
        assert files[0].file_id == pf.file_id

    def test_list_files_with_partition_filter(self, lake_store_fixture):
        store = lake_store_fixture
        store.register_file("tbl_test", "20261101", rows=10, bytes_=1280)
        store.register_file("tbl_test", "20261102", rows=20, bytes_=2560)

        f1 = store.list_files("tbl_test", "20261101")
        f2 = store.list_files("tbl_test", "20261102")
        assert len(f1) == 1
        assert len(f2) == 1
        assert f1[0].partition_key == "20261101"

    def test_remove_files(self, lake_store_fixture):
        store = lake_store_fixture
        pf1 = store.register_file("tbl_test", "20261101", rows=10, bytes_=1280)
        pf2 = store.register_file("tbl_test", "20261101", rows=20, bytes_=2560)
        removed = store.remove_files("tbl_test", [pf1.file_id])
        assert removed == 1
        files = store.list_files("tbl_test")
        assert len(files) == 1
        assert files[0].file_id == pf2.file_id

    def test_replace_file_list_atomic(self, lake_store_fixture):
        store = lake_store_fixture
        pf1 = store.register_file("tbl_test", "20261101", rows=10, bytes_=1280)
        pf2 = store.register_file("tbl_test", "20261101", rows=20, bytes_=2560)
        old_ids = [pf1.file_id, pf2.file_id]
        new_pf = PartitionFile("n-fid-xxx", "tbl_test", "20261101", 30, 3000, "m_xx", time.time())
        store.replace_file_list("tbl_test", old_ids, [new_pf])
        files = store.list_files("tbl_test")
        assert len(files) == 1
        assert files[0].file_id == "n-fid-xxx"


class TestSnapshotChain:
    def test_create_and_mark_snapshot(self, lake_store_fixture):
        store = lake_store_fixture
        pf = store.register_file("tbl_test", "20261101", rows=100, bytes_=25600)
        snap = store.create_snapshot("tbl_test", [pf.file_id], added_rows=100, deleted_rows=0)
        assert snap.status == "generating"
        store.mark_snapshot_available("tbl_test", snap.snapshot_id)
        assert store.get_snapshot("tbl_test", snap.snapshot_id).status == "available"

    def test_snapshot_time_travel(self, lake_store_fixture):
        store = lake_store_fixture
        pf = store.register_file("tbl_test", "20261101", rows=100, bytes_=25600)
        t0 = time.time()
        snap = store.create_snapshot("tbl_test", [pf.file_id], added_rows=100, deleted_rows=0)
        store.mark_snapshot_available("tbl_test", snap.snapshot_id)
        result = store.get_snapshot_at_time("tbl_test", t0 + 1)
        assert result is not None
        assert result.snapshot_id == snap.snapshot_id

    def test_snapshot_ancestor_chain(self, lake_store_fixture):
        store = lake_store_fixture
        pf1 = store.register_file("tbl_test", "20261101", rows=10, bytes_=1280)
        snap1 = store.create_snapshot("tbl_test", [pf1.file_id], added_rows=10)
        store.mark_snapshot_available("tbl_test", snap1.snapshot_id)

        pf2 = store.register_file("tbl_test", "20261102", rows=20, bytes_=2560)
        snap2 = store.create_snapshot("tbl_test", [pf2.file_id],
                                      parent_snapshot=snap1.snapshot_id, added_rows=20)
        store.mark_snapshot_available("tbl_test", snap2.snapshot_id)

        snaps = store.list_snapshots("tbl_test")
        assert len(snaps) == 2
        assert snaps[1].parent_snapshot == snaps[0].snapshot_id

    def test_mark_snapshot_expired(self, lake_store_fixture):
        store = lake_store_fixture
        pf = store.register_file("tbl_test", "20261101", rows=100, bytes_=25600)
        snap = store.create_snapshot("tbl_test", [pf.file_id])
        store.mark_snapshot_available("tbl_test", snap.snapshot_id)
        store.mark_snapshot_expired("tbl_test", snap.snapshot_id)
        assert store.get_snapshot("tbl_test", snap.snapshot_id).status == "expired"


class TestWatermark:
    def test_create_and_advance_watermark(self, lake_store_fixture):
        store = lake_store_fixture
        wm = store.set_watermark("tbl_test", "event_time", "2026-01-01T00:00:00", "append")
        assert wm.committed_value == "2026-01-01T00:00:00"

        store.advance_watermark("tbl_test", "2026-01-02T00:00:00")
        store.commit_watermark("tbl_test")
        wm2 = store.get_watermark("tbl_test")
        assert wm2.committed_value == "2026-01-02T00:00:00"
        assert wm2.pending_value is None

    def test_list_watermarks(self, lake_store_fixture):
        store = lake_store_fixture
        store.set_watermark("tbl_a", "col_a", "v1")
        store.set_watermark("tbl_b", "col_b", "v2")
        wms = store.list_watermarks()
        assert len(wms) == 2


class TestBatchAndQuarantine:
    def test_store_and_get_batch(self, lake_store_fixture):
        store = lake_store_fixture
        rows = [{"k": "v1"}, {"k": "v2"}]
        br = store.store_batch("b123", "tbl_test", "src1", rows, "2026-01-01", "2026-01-02")
        assert br.row_count == 2
        assert br.checksum != ""
        retrieved = store.get_batch("b123")
        assert retrieved is not None
        assert retrieved.row_count == 2

    def test_update_batch_status(self, lake_store_fixture):
        store = lake_store_fixture
        store.store_batch("b123", "tbl_test", "src1", [{"k": "v"}], "2026-01-01", "2026-01-02")
        store.update_batch_status("b123", "ingested", "snap-001")
        br = store.get_batch("b123")
        assert br.status == "ingested"
        assert br.snapshot_id == "snap-001"

    def test_quarantine_and_release(self, lake_store_fixture):
        store = lake_store_fixture
        rows = [{"k": "v1"}, {"k": "v2"}]
        store.quarantine_rows("b123", "QR-1", "金额异常", rows)
        qr = store.list_quarantine("b123")
        assert len(qr) == 2
        assert qr[0]["_quarantine_rule"] == "QR-1"
        released = store.release_quarantine("b123")
        assert len(released) == 2
        assert "_quarantine_rule" not in released[0]


class TestMergeCheckpoint:
    def test_save_and_recover_checkpoint(self, lake_store_fixture):
        store = lake_store_fixture
        store.save_merge_checkpoint("merge-1", ["f1", "f2", "f3"])
        cp = store.get_merge_checkpoint("merge-1")
        assert cp is not None
        assert cp["partial_file_ids"] == ["f1", "f2", "f3"]
        store.clear_merge_checkpoint("merge-1")
        assert store.get_merge_checkpoint("merge-1") is None

    def test_merge_checkpoint_nonexistent(self, lake_store_fixture):
        store = lake_store_fixture
        assert store.get_merge_checkpoint("nonexistent") is None


class TestWriteLock:
    def test_lock_acquire_release(self, lake_store_fixture):
        store = lake_store_fixture
        lock = store.acquire_write_lock("tbl_test")
        assert lock is not None
        store.release_write_lock("tbl_test")


class TestStats:
    def test_stats_snapshot(self, lake_store_fixture):
        store = lake_store_fixture
        store.register_file("tbl_test", "20261101", rows=100, bytes_=25600)
        store.register_file("tbl_test", "20261101", rows=50, bytes_=12800)
        stats = store.stats_snapshot("tbl_test")
        assert stats["file_count"] == 2
        assert stats["total_rows"] == 150
        assert stats["total_bytes"] == 38400
        assert stats["partition_count"] == 1