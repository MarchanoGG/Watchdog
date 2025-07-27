"""
Checksum helpers

• sha256_stream(path) - cryptographic baseline
• xxh3_stream(path)  - 10x faster pre-screen (uses xxhash if installed)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

try:
    import xxhash  # type: ignore
except ModuleNotFoundError:  # noqa: PERF203
    xxhash = None  # graceful fallback


_CHUNK = 4 << 20  # 4 MiB


def sha256_stream(path: Path) -> str:
    """Return hex-digest while reading file once."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def xxh3_stream(path: Path) -> Optional[str]:
    """Return 128-bit xxh3 hex or None if library missing."""
    if xxhash is None:
        return None
    hasher = xxhash.xxh3_128()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
