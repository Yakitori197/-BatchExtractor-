"""
7-Zip CLI wrapper for archive extraction.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from .config import SEVEN_ZIP_BINARIES


class SevenZipNotFoundError(Exception):
    """Raised when 7-Zip is not found in PATH."""
    pass


class ExtractionError(Exception):
    """Raised when archive extraction fails."""
    pass


def find_7z_binary() -> Optional[str]:
    """
    Find the 7-Zip binary in PATH.
    
    Returns:
        The path to the 7z binary, or None if not found
    """
    for binary in SEVEN_ZIP_BINARIES:
        path = shutil.which(binary)
        if path:
            return path
    return None


def check_7z_available() -> Tuple[bool, str]:
    """
    Check if 7-Zip is available and get its version.
    
    Returns:
        Tuple of (is_available, version_or_error_message)
    """
    binary = find_7z_binary()
    if not binary:
        return False, (
            "7-Zip not found in PATH. Please install:\n"
            "  Windows: choco install 7zip  OR  download from https://7-zip.org\n"
            "  macOS:   brew install p7zip\n"
            "  Linux:   sudo apt install p7zip-full  OR  sudo dnf install p7zip-plugins"
        )
    
    try:
        result = subprocess.run(
            [binary],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Parse version from output
        for line in result.stdout.split("\n"):
            if "7-Zip" in line or "p7zip" in line:
                return True, line.strip()
        return True, f"7-Zip found at {binary}"
    except Exception as e:
        return False, f"Error checking 7-Zip: {e}"


def extract_archive(
    archive_path: Path,
    output_dir: Path,
    password: Optional[str] = None,
    overwrite: bool = True
) -> Tuple[bool, str]:
    """
    Extract an archive using 7-Zip.
    
    Args:
        archive_path: Path to the archive file
        output_dir: Directory to extract files to
        password: Optional password for encrypted archives
        overwrite: Whether to overwrite existing files
        
    Returns:
        Tuple of (success, message)
    """
    binary = find_7z_binary()
    if not binary:
        raise SevenZipNotFoundError("7-Zip not found in PATH")
    
    # Build command
    # x = extract with full paths
    # -o = output directory
    # -y = assume Yes on all queries (auto overwrite)
    # -p = password
    cmd = [binary, "x", str(archive_path), f"-o{output_dir}"]
    
    if overwrite:
        cmd.append("-y")
    else:
        cmd.append("-aos")  # Skip extracting of existing files
    
    if password:
        cmd.append(f"-p{password}")
    else:
        # Try with empty password first (handles non-encrypted archives)
        cmd.append("-p")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for large archives
        )
        
        if result.returncode == 0:
            return True, "Extraction successful"
        elif result.returncode == 2:
            # Fatal error - likely password protected or corrupted
            if "Wrong password" in result.stderr or "wrong password" in result.stdout.lower():
                return False, "Wrong password or archive is password protected"
            return False, f"Fatal error: {result.stderr or result.stdout}"
        elif result.returncode == 1:
            # Warning (non-fatal)
            return True, f"Extraction completed with warnings: {result.stderr or result.stdout}"
        else:
            return False, f"Extraction failed (code {result.returncode}): {result.stderr or result.stdout}"
            
    except subprocess.TimeoutExpired:
        return False, "Extraction timed out (exceeded 1 hour)"
    except Exception as e:
        return False, f"Extraction error: {e}"


def list_archive_contents(archive_path: Path, password: Optional[str] = None) -> Tuple[bool, list]:
    """
    List contents of an archive without extracting.
    
    Args:
        archive_path: Path to the archive file
        password: Optional password for encrypted archives
        
    Returns:
        Tuple of (success, list_of_files_or_error)
    """
    binary = find_7z_binary()
    if not binary:
        raise SevenZipNotFoundError("7-Zip not found in PATH")
    
    cmd = [binary, "l", "-slt", str(archive_path)]
    
    if password:
        cmd.append(f"-p{password}")
    else:
        cmd.append("-p")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return False, [result.stderr or result.stdout]
        
        # Parse output to get file list
        files = []
        current_file = {}
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line.startswith("Path = "):
                if current_file and "Path" in current_file:
                    files.append(current_file)
                current_file = {"Path": line[7:]}
            elif line.startswith("Size = "):
                current_file["Size"] = line[7:]
            elif line.startswith("Attributes = "):
                current_file["Attributes"] = line[13:]
        
        if current_file and "Path" in current_file:
            files.append(current_file)
        
        # Filter out directories (attributes starting with D)
        files = [f for f in files if not f.get("Attributes", "").startswith("D")]
        
        return True, files
        
    except subprocess.TimeoutExpired:
        return False, ["Listing timed out"]
    except Exception as e:
        return False, [str(e)]
