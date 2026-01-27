"""
Configuration constants and supported archive formats.
"""

from pathlib import Path
from typing import FrozenSet

# Supported archive extensions (lowercase)
ARCHIVE_EXTENSIONS: FrozenSet[str] = frozenset({
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".tbz2",
    ".xz",
    ".txz",
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".lzma",
    ".cab",
    ".iso",
    ".arj",
    ".lzh",
    ".z",
})

# Common double extensions (handled specially)
DOUBLE_EXTENSIONS: FrozenSet[str] = frozenset({
    ".tar.gz",
    ".tar.bz2",
    ".tar.xz",
    ".tar.lzma",
})

# Default settings
DEFAULT_MAX_ROUNDS = 50
DEFAULT_WORKERS = 4
HASH_LENGTH = 8

# 7z binary names by platform
SEVEN_ZIP_BINARIES = ["7z", "7za", "7zz"]


def is_archive(path: Path) -> bool:
    """
    Check if a file is a recognized archive format.
    
    Args:
        path: Path to the file
        
    Returns:
        True if the file is a recognized archive format
    """
    name_lower = path.name.lower()
    
    # Check double extensions first
    for ext in DOUBLE_EXTENSIONS:
        if name_lower.endswith(ext):
            return True
    
    # Check single extensions
    suffix = path.suffix.lower()
    return suffix in ARCHIVE_EXTENSIONS


def get_archive_extension(path: Path) -> str:
    """
    Get the archive extension (handling double extensions like .tar.gz).
    
    Args:
        path: Path to the file
        
    Returns:
        The archive extension (e.g., '.tar.gz' or '.zip')
    """
    name_lower = path.name.lower()
    
    for ext in DOUBLE_EXTENSIONS:
        if name_lower.endswith(ext):
            return ext
    
    return path.suffix.lower()
