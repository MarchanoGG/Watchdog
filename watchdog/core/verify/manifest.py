"""
Manifest helper.

• One JSON file per server, written right after a successful backup.
• Describes every artefact (tarball, SQL dump, …) so the Verifier
  can recreate exactly what “should” be on disk - without scanning
  directories.

Example JSON:
{
  "server": "ServerName",
  "pulse": "2025-07-27_22-30-02",
  "artifacts": [
    {
      "path": "sites.tar.gz",
      "sha256": "abc123…",
      "size": 1843509231,
      "type": "tar"
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any


class Manifest:
    SCHEMA_VERSION = 1

    def __init__(self, server: str, pulse: str) -> None:
        self.server = server
        self.pulse = pulse
        self.artifacts: List[Dict[str, Any]] = []

    # Public API

    def add_artifact(self, path: Path, sha256: str, size: int, art_type: str, xxh3: str | None = None) -> None:
        """Register one file in the manifest."""
        self.artifacts.append(
            {
                "path": path.name,
                "sha256": sha256,
                "size": size,
                "type": art_type,
                "xxh3": xxh3,
            }
        )

    def save(self, dest_dir: Path) -> Path:
        """Write manifest JSON to `<dest_dir>/<server>.json`."""
        dest_dir.mkdir(parents=True, exist_ok=True)
        file_path = dest_dir / f"{self.server}.json"
        data = {
            "schema": self.SCHEMA_VERSION,
            "server": self.server,
            "pulse": self.pulse,
            "artifacts": self.artifacts,
        }
        file_path.write_text(json.dumps(data, indent=2))
        return file_path

    # Helpers

    @classmethod
    def load(cls, file_path: Path) -> "Manifest":
        """Load an existing manifest from disk."""
        data = json.loads(file_path.read_text())
        man = cls(server=data["server"], pulse=data["pulse"])
        man.artifacts = data["artifacts"]
        return man
