"""
Integrity checks for gzip-compressed tarballs.
All checks are streaming - no extraction to disk.
"""

from __future__ import annotations

import gzip
import tarfile
from pathlib import Path
from typing import Tuple


def gzip_valid(path: Path) -> Tuple[bool, str]:
    """Run `gzip -t` equivalent using Python stdlib."""
    try:
        with gzip.open(path, "rb") as fh:
            while fh.read(4 << 20):
                pass
        return True, ""
    except OSError as exc:
        return False, str(exc)


def tar_structure_valid(path: Path) -> Tuple[bool, str]:
    """Ensure tar headers are readable."""
    try:
        with tarfile.open(path, "r:gz") as tf:
            for _ in tf:  # iterate headers only
                pass
        return True, ""
    except tarfile.TarError as exc:
        return False, str(exc)
