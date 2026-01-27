"""
Filename conflict resolution utilities.
"""

import hashlib
from pathlib import Path
from typing import Set, Tuple

from .config import HASH_LENGTH


class FilenameResolver:
    """
    Resolves filename conflicts by appending hash or counter suffixes.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the resolver.
        
        Args:
            output_dir: The output directory where files will be placed
        """
        self.output_dir = output_dir
        self._used_names: Set[str] = set()
        
        # Initialize with existing files in output directory
        if output_dir.exists():
            for f in output_dir.iterdir():
                if f.is_file():
                    self._used_names.add(f.name.lower())
    
    def _split_filename(self, filename: str) -> Tuple[str, str]:
        """
        Split filename into stem and extension, handling special cases.
        
        Args:
            filename: The filename to split
            
        Returns:
            Tuple of (stem, extension)
        """
        path = Path(filename)
        name_lower = filename.lower()
        
        # Handle double extensions
        double_exts = [".tar.gz", ".tar.bz2", ".tar.xz", ".tar.lzma"]
        for ext in double_exts:
            if name_lower.endswith(ext):
                stem = filename[:-len(ext)]
                return stem, ext
        
        return path.stem, path.suffix
    
    def _compute_content_hash(self, source_path: Path) -> str:
        """
        Compute a short hash of file content for unique naming.
        
        Args:
            source_path: Path to the source file
            
        Returns:
            8-character hash string
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(source_path, "rb") as f:
                # Read first 64KB for hashing (fast approximation)
                chunk = f.read(65536)
                sha256_hash.update(chunk)
            return sha256_hash.hexdigest()[:HASH_LENGTH]
        except Exception:
            # Fallback to random-like hash
            import time
            return hashlib.md5(str(time.time_ns()).encode()).hexdigest()[:HASH_LENGTH]
    
    def resolve(
        self,
        original_filename: str,
        source_path: Path = None
    ) -> Tuple[str, bool]:
        """
        Resolve a filename to a unique name in the output directory.
        
        Args:
            original_filename: The original filename
            source_path: Optional path to source file (for content-based hashing)
            
        Returns:
            Tuple of (resolved_filename, was_renamed)
        """
        name_lower = original_filename.lower()
        
        # If no conflict, use original name
        if name_lower not in self._used_names:
            self._used_names.add(name_lower)
            return original_filename, False
        
        stem, ext = self._split_filename(original_filename)
        
        # Strategy 1: Try with content hash
        if source_path and source_path.exists():
            content_hash = self._compute_content_hash(source_path)
            new_name = f"{stem}__{content_hash}{ext}"
            if new_name.lower() not in self._used_names:
                self._used_names.add(new_name.lower())
                return new_name, True
        
        # Strategy 2: Try with counter
        counter = 1
        while True:
            new_name = f"{stem}__{counter}{ext}"
            if new_name.lower() not in self._used_names:
                self._used_names.add(new_name.lower())
                return new_name, True
            counter += 1
            
            # Safety limit
            if counter > 100000:
                raise RuntimeError(f"Too many filename conflicts for {original_filename}")
    
    def check_conflict(self, filename: str) -> bool:
        """
        Check if a filename would conflict.
        
        Args:
            filename: The filename to check
            
        Returns:
            True if there would be a conflict
        """
        return filename.lower() in self._used_names
    
    def reserve_name(self, filename: str) -> None:
        """
        Reserve a filename without actually using it.
        
        Args:
            filename: The filename to reserve
        """
        self._used_names.add(filename.lower())
    
    def get_output_path(
        self,
        original_filename: str,
        source_path: Path = None
    ) -> Tuple[Path, str, bool]:
        """
        Get the full output path for a file, resolving conflicts.
        
        Args:
            original_filename: The original filename
            source_path: Optional path to source file
            
        Returns:
            Tuple of (output_path, final_filename, was_renamed)
        """
        resolved_name, was_renamed = self.resolve(original_filename, source_path)
        output_path = self.output_dir / resolved_name
        return output_path, resolved_name, was_renamed
