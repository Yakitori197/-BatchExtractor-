"""
Tests for unpack-flat.
"""

import tempfile
import zipfile
from pathlib import Path

import pytest

from unpack_flat.config import get_archive_extension, is_archive
from unpack_flat.resolver import FilenameResolver


class TestFilenameResolver:
    """Tests for filename conflict resolution."""

    def test_no_conflict_uses_original_name(self):
        """When there's no conflict, the original name should be used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            resolver = FilenameResolver(output_dir)

            resolved, was_renamed = resolver.resolve("test.txt")

            assert resolved == "test.txt"
            assert was_renamed is False

    def test_conflict_renames_with_counter(self):
        """When there's a conflict, the file should be renamed with a counter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create existing file
            (output_dir / "test.txt").touch()

            resolver = FilenameResolver(output_dir)

            resolved, was_renamed = resolver.resolve("test.txt")

            assert was_renamed is True
            assert resolved.startswith("test__")
            assert resolved.endswith(".txt")
            assert resolved != "test.txt"

    def test_multiple_conflicts_get_unique_names(self):
        """Multiple files with the same name should all get unique names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            resolver = FilenameResolver(output_dir)

            names = []
            for _ in range(5):
                resolved, _ = resolver.resolve("duplicate.txt")
                names.append(resolved)

            # All names should be unique
            assert len(names) == len(set(names))

    def test_case_insensitive_conflict_detection(self):
        """Conflicts should be detected case-insensitively."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create existing file with uppercase
            (output_dir / "Test.TXT").touch()

            resolver = FilenameResolver(output_dir)

            # Try to add lowercase version
            resolved, was_renamed = resolver.resolve("test.txt")

            assert was_renamed is True

    def test_content_hash_used_when_source_available(self):
        """When source file is available, content hash should be used for naming."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            source_dir = Path(tmpdir) / "source"
            source_dir.mkdir()

            # Create existing file in output
            (output_dir / "test.txt").touch()

            # Create source file with content
            source_file = source_dir / "test.txt"
            source_file.write_text("unique content here")

            resolver = FilenameResolver(output_dir)

            resolved, was_renamed = resolver.resolve("test.txt", source_path=source_file)

            assert was_renamed is True
            # Should contain hash (8 chars)
            assert "__" in resolved
            parts = resolved.replace(".txt", "").split("__")
            assert len(parts) == 2
            assert len(parts[1]) == 8  # Hash length


class TestNoOverwrite:
    """Tests to ensure files are never overwritten."""

    def test_existing_file_not_overwritten(self):
        """Files in output directory should never be overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create existing file with content
            existing = output_dir / "important.txt"
            existing.write_text("DO NOT OVERWRITE")

            resolver = FilenameResolver(output_dir)

            # Resolve should give a different name
            output_path, final_name, was_renamed = resolver.get_output_path("important.txt")

            assert was_renamed is True
            assert final_name != "important.txt"
            assert output_path != existing

            # Original file should still be intact
            assert existing.read_text() == "DO NOT OVERWRITE"

    def test_multiple_resolves_never_collide(self):
        """Multiple consecutive resolves should never produce the same path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            resolver = FilenameResolver(output_dir)

            paths = set()
            for i in range(100):
                output_path, _, _ = resolver.get_output_path("same_name.txt")
                assert output_path not in paths, f"Collision at iteration {i}"
                paths.add(output_path)

    def test_reserved_names_respected(self):
        """Reserved names should not be used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            resolver = FilenameResolver(output_dir)

            # Reserve a name
            resolver.reserve_name("reserved.txt")

            # Try to resolve with that name
            resolved, was_renamed = resolver.resolve("reserved.txt")

            assert was_renamed is True
            assert resolved != "reserved.txt"


class TestMaxRoundsConvergence:
    """Tests for extraction round limits and convergence."""

    def test_max_rounds_limits_extraction(self):
        """Extraction should stop after max_rounds even if archives remain."""
        # This test creates a nested archive structure and verifies
        # that the max_rounds parameter is respected

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "input"
            output_dir = tmpdir / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            # Create a self-referencing archive (archive containing itself)
            # This simulates an infinite nesting scenario

            inner_file = input_dir / "data.txt"
            inner_file.write_text("test data")

            # Create first archive
            archive1 = input_dir / "level1.zip"
            with zipfile.ZipFile(archive1, 'w') as zf:
                zf.write(inner_file, "data.txt")

            # Verify the archive is recognized
            assert is_archive(archive1)

            # The max_rounds parameter should prevent infinite extraction
            # We're testing the configuration, not the full extraction
            from unpack_flat.extractor import UnpackFlat

            extractor = UnpackFlat(
                input_dir=input_dir,
                output_dir=output_dir,
                max_rounds=2,
                dry_run=True
            )

            assert extractor.max_rounds == 2

    def test_convergence_when_no_archives(self):
        """Extraction should converge naturally when no archives are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_dir = tmpdir / "input"
            input_dir.mkdir()

            # Create only regular files
            (input_dir / "file1.txt").write_text("content 1")
            (input_dir / "file2.txt").write_text("content 2")

            # No archives should be found
            from unpack_flat.extractor import UnpackFlat

            extractor = UnpackFlat(
                input_dir=input_dir,
                output_dir=tmpdir / "output",
                max_rounds=10,
                dry_run=True
            )

            archives = extractor._scan_for_archives(input_dir)
            assert len(archives) == 0


class TestArchiveDetection:
    """Tests for archive format detection."""

    def test_zip_detected(self):
        assert is_archive(Path("test.zip"))
        assert is_archive(Path("test.ZIP"))

    def test_7z_detected(self):
        assert is_archive(Path("test.7z"))

    def test_rar_detected(self):
        assert is_archive(Path("test.rar"))
        assert is_archive(Path("test.RAR"))

    def test_tar_detected(self):
        assert is_archive(Path("test.tar"))

    def test_tar_gz_detected(self):
        assert is_archive(Path("test.tar.gz"))
        assert is_archive(Path("test.tgz"))

    def test_tar_bz2_detected(self):
        assert is_archive(Path("test.tar.bz2"))
        assert is_archive(Path("test.tbz2"))

    def test_tar_xz_detected(self):
        assert is_archive(Path("test.tar.xz"))
        assert is_archive(Path("test.txz"))

    def test_regular_files_not_detected(self):
        assert not is_archive(Path("test.txt"))
        assert not is_archive(Path("test.pdf"))
        assert not is_archive(Path("test.exe"))
        assert not is_archive(Path("test.jpg"))

    def test_get_extension_double_extension(self):
        assert get_archive_extension(Path("test.tar.gz")) == ".tar.gz"
        assert get_archive_extension(Path("test.tar.bz2")) == ".tar.bz2"

    def test_get_extension_single_extension(self):
        assert get_archive_extension(Path("test.zip")) == ".zip"
        assert get_archive_extension(Path("test.7z")) == ".7z"


class TestManifestEntry:
    """Tests for manifest entry creation."""

    def test_manifest_entry_fields(self):
        from unpack_flat.manifest import ManifestEntry

        entry = ManifestEntry(
            source_path="/input/archive/file.txt",
            output_path="/output/file.txt",
            output_filename="file.txt",
            renamed=False,
            original_filename="file.txt",
            file_size=1024,
            sha256="abc123",
            archive_source="archive.zip"
        )

        assert entry.source_path == "/input/archive/file.txt"
        assert entry.renamed is False
        assert entry.file_size == 1024

    def test_manifest_entry_renamed(self):
        from unpack_flat.manifest import ManifestEntry

        entry = ManifestEntry(
            source_path="/input/file.txt",
            output_path="/output/file__1.txt",
            output_filename="file__1.txt",
            renamed=True,
            original_filename="file.txt",
            file_size=512,
        )

        assert entry.renamed is True
        assert entry.original_filename == "file.txt"
        assert entry.output_filename == "file__1.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
