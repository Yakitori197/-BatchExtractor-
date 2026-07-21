"""
Manifest file writer for tracking extracted files.
"""

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from types import TracebackType
from typing import Literal, Optional, TextIO


@dataclass
class ManifestEntry:
    """A single entry in the manifest."""
    source_path: str  # Original path within the archive hierarchy
    output_path: str  # Final output path
    output_filename: str  # Final filename
    renamed: bool  # Whether the file was renamed due to conflict
    original_filename: str  # Original filename before renaming
    file_size: int  # File size in bytes
    sha256: Optional[str] = None  # SHA256 hash (optional)
    archive_source: str = ""  # Which archive this file came from


class ManifestWriter:
    """
    Writes manifest files in JSONL or CSV format.
    """

    def __init__(
        self,
        output_path: Path,
        format: Literal["jsonl", "csv"] = "jsonl",
        compute_hash: bool = True
    ):
        """
        Initialize the manifest writer.
        
        Args:
            output_path: Path to the manifest file
            format: Output format ('jsonl' or 'csv')
            compute_hash: Whether to compute SHA256 hashes
        """
        self.output_path = output_path
        self.format = format
        self.compute_hash = compute_hash
        self.entries: list[ManifestEntry] = []
        self._file_handle: Optional[TextIO] = None
        self._csv_writer: Optional[csv.DictWriter[str]] = None

    def __enter__(self) -> "ManifestWriter":
        """Open the manifest file for writing."""
        # Bind to locals first: the attributes are Optional, so using them
        # directly here would neither type-check nor be None-safe.
        handle = open(self.output_path, "w", encoding="utf-8", newline="")
        self._file_handle = handle

        if self.format == "csv":
            writer: csv.DictWriter[str] = csv.DictWriter(
                handle,
                fieldnames=[
                    "source_path", "output_path", "output_filename",
                    "renamed", "original_filename", "file_size",
                    "sha256", "archive_source"
                ]
            )
            self._csv_writer = writer
            writer.writeheader()

        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Close the manifest file."""
        if self._file_handle:
            self._file_handle.close()

    @staticmethod
    def compute_sha256(file_path: Path) -> str:
        """
        Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex-encoded SHA256 hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def add_entry(
        self,
        source_path: Path,
        output_path: Path,
        renamed: bool,
        original_filename: str,
        archive_source: str = ""
    ) -> ManifestEntry:
        """
        Add an entry to the manifest.
        
        Args:
            source_path: Original source path
            output_path: Final output path (must exist)
            renamed: Whether the file was renamed
            original_filename: Original filename before renaming
            archive_source: Which archive this file came from
            
        Returns:
            The created ManifestEntry
        """
        file_size = output_path.stat().st_size if output_path.exists() else 0

        sha256 = None
        if self.compute_hash and output_path.exists():
            try:
                sha256 = self.compute_sha256(output_path)
            except Exception:
                pass  # Skip hash on error

        entry = ManifestEntry(
            source_path=str(source_path),
            output_path=str(output_path),
            output_filename=output_path.name,
            renamed=renamed,
            original_filename=original_filename,
            file_size=file_size,
            sha256=sha256,
            archive_source=archive_source
        )

        self.entries.append(entry)
        self._write_entry(entry)

        return entry

    def _write_entry(self, entry: ManifestEntry) -> None:
        """Write a single entry to the manifest file."""
        if not self._file_handle:
            return

        if self.format == "jsonl":
            self._file_handle.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
            self._file_handle.flush()
        elif self.format == "csv" and self._csv_writer:
            self._csv_writer.writerow(asdict(entry))
            self._file_handle.flush()

    def get_stats(self) -> dict:
        """
        Get statistics about the manifest entries.
        
        Returns:
            Dictionary with statistics
        """
        total_size = sum(e.file_size for e in self.entries)
        renamed_count = sum(1 for e in self.entries if e.renamed)

        return {
            "total_files": len(self.entries),
            "renamed_files": renamed_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
