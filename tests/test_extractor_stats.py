"""
ExtractionStats 計數的回歸測試。

背景：scanned_files 原本在 _scan_for_archives 內用 `+= 1` 累加，而該函式
每輪會被呼叫兩次（run() 掃一次、_run_extraction_round 又掃一次），且每一輪
都會重新走訪整個工作目錄。結果摘要表的「Files scanned」數字遠大於實際檔案數。
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unpack_flat.extractor import UnpackFlat


def _make_extractor(tmp_path: Path) -> UnpackFlat:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    extractor = UnpackFlat(input_dir=input_dir, output_dir=output_dir)
    extractor._work_dir = input_dir
    return extractor


class TestScannedFilesCount:
    def test_counts_each_file_once(self, tmp_path):
        extractor = _make_extractor(tmp_path)
        work = extractor.work_dir
        for name in ("a.txt", "b.txt", "c.txt"):
            (work / name).write_text("x")

        extractor._scan_for_archives(work)
        assert extractor.stats.scanned_files == 3

    def test_rescanning_does_not_inflate_the_count(self, tmp_path):
        """每輪都會重掃同一個目錄；同一個檔案不可以被重複計數。"""
        extractor = _make_extractor(tmp_path)
        work = extractor.work_dir
        for name in ("a.txt", "b.txt", "c.txt"):
            (work / name).write_text("x")

        extractor._scan_for_archives(work)
        extractor._scan_for_archives(work)
        extractor._scan_for_archives(work)

        assert extractor.stats.scanned_files == 3  # 不是 9

    def test_counts_files_in_subdirectories(self, tmp_path):
        extractor = _make_extractor(tmp_path)
        work = extractor.work_dir
        (work / "a.txt").write_text("x")
        nested = work / "sub" / "deep"
        nested.mkdir(parents=True)
        (nested / "b.txt").write_text("x")

        extractor._scan_for_archives(work)
        assert extractor.stats.scanned_files == 2

    def test_newly_appeared_files_are_added(self, tmp_path):
        """解壓後新檔案出現，重掃時應該把新檔算進去（但舊檔仍只算一次）。"""
        extractor = _make_extractor(tmp_path)
        work = extractor.work_dir
        (work / "a.txt").write_text("x")

        extractor._scan_for_archives(work)
        assert extractor.stats.scanned_files == 1

        (work / "b.txt").write_text("x")  # 模擬解壓產生的新檔
        extractor._scan_for_archives(work)
        assert extractor.stats.scanned_files == 2

    def test_empty_dir_counts_zero(self, tmp_path):
        extractor = _make_extractor(tmp_path)
        extractor._scan_for_archives(extractor.work_dir)
        assert extractor.stats.scanned_files == 0


class TestWorkDirGuard:
    def test_work_dir_raises_before_setup(self, tmp_path):
        """_work_dir 未設定時存取應明確報錯，而不是把 None 傳下去。"""
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()
        extractor = UnpackFlat(input_dir=input_dir, output_dir=output_dir)

        with pytest.raises(RuntimeError):
            _ = extractor.work_dir
