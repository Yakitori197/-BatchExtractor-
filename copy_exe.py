"""Helper script to copy EXE with Chinese filename"""
import shutil
from pathlib import Path

src = Path("dist/BatchExtractor.exe")
dst = Path("壓縮檔工具.exe")

if src.exists():
    shutil.copy2(src, dst)
    print(f"Created: {dst}")
else:
    print("Error: dist/BatchExtractor.exe not found")
