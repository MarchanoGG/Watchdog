"""
Sanity checks for gzipped MySQL dumps.
We don't parse SQL – just verify header/footer strings.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Tuple


HEADER_TOKEN = b"-- MySQL dump"
FOOTER_TOKEN = b"-- Dump completed"


def dump_header_footer_ok(path: Path) -> Tuple[bool, str]:
    """Return True if header and footer look normal."""
    try:
        with gzip.open(path, "rb") as fh:
            head = fh.readline(1024)
        with gzip.open(path, "rb") as fh:
            fh.seek(-min(8192, fh.tell()), 2)
            tail = fh.read()
    except OSError as exc:
        return False, f"gzip error: {exc}"

    if HEADER_TOKEN not in head:
        return False, "header token missing"
    if FOOTER_TOKEN not in tail:
        return False, "footer token missing"
    return True, ""
