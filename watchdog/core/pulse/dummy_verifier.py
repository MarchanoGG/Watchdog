"""Extremely simple placeholder – replace with real checksum logic later."""
from pathlib import Path
from typing import Dict, Any


class DummyVerifier:
    def verify(self, backup_root: Path) -> Dict[str, Any]:
        # In het echt: checksums, tar -tzf, database dumps inspecteren, enz.
        files = list(backup_root.rglob("*.tar.gz"))
        return {
            "overall": "PASSED" if files else "FAILED",
            "files_checked": len(files),
            "sample": [f.name for f in files[:3]],
        }
