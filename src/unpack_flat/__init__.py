"""
unpack-flat: Recursively extract nested archives and flatten all files to a single output directory.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .extractor import UnpackFlat
from .manifest import ManifestWriter

__all__ = ["UnpackFlat", "ManifestWriter", "__version__"]
