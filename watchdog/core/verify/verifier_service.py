"""
VerifierService – orchestrates all integrity checks for one Pulse.
Returns dict with `overall`, `errors`, `warnings`, `metrics`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from watchdog.utils.logger import WatchdogLogger
from .checksum import sha256_stream, xxh3_stream
from .tar_inspector import gzip_valid, tar_structure_valid
from .sql_inspector import dump_header_footer_ok
from .manifest import Manifest


class VerifierService:
    """High-level façade used by PulseService."""

    def __init__(self) -> None:
        self.logger = WatchdogLogger("verify")

    # ------------------------------------------------------------------ #
    # Public API

    def verify_pulse(self, pulse_dir: Path) -> Dict[str, Any]:
        """
        Verify every server manifest inside `pulse_dir`.
        Returns aggregated dict that PulseService will embed to Discord.
        """
        errors: List[str] = []
        warnings: List[str] = []
        metrics: Dict[str, Any] = {"servers": 0, "files_checked": 0}

        manifest_files = list(pulse_dir.glob("*.json"))
        if not manifest_files:
            errors.append("No manifest files found!")
            return _result(errors, warnings, metrics)

        for mf in manifest_files:
            self.logger.info(f"Loading manifest {mf}")
            man = Manifest.load(mf)
            metrics["servers"] += 1
            for art in man.artifacts:
                art_path = pulse_dir / man.server.lower() / art["path"]
                ok, w = self._verify_artifact(art, art_path)
                metrics["files_checked"] += 1
                if not ok:
                    errors.append(f"{man.server}/{art['path']}: {w}")
                elif w:  # soft warning
                    warnings.append(f"{man.server}/{art['path']}: {w}")

        return _result(errors, warnings, metrics)

    # ------------------------------------------------------------------ #
    # Internals

    def _verify_artifact(
        self, spec: Dict[str, Any], path: Path
    ) -> Tuple[bool, str]:
        if not path.exists():
            return False, "file missing on disk"

        # 1 · Size
        if path.stat().st_size != spec["size"]:
            return False, "size mismatch"

        # 2 · Hash
        # fast pre-screen (optional)
        if (fast := xxh3_stream(path)) and fast == spec.get("xxh3"):
            pass  # cheap success!
        else:
            sha = sha256_stream(path)
            if sha != spec["sha256"]:
                return False, "SHA-256 mismatch"

        # 3 · Type-specific checks
        if spec["type"] == "tar":
            ok, msg = gzip_valid(path)
            if not ok:
                return False, f"gzip invalid: {msg}"
            ok, msg = tar_structure_valid(path)
            if not ok:
                return False, f"tar header error: {msg}"
        elif spec["type"] == "mysql":
            ok, msg = dump_header_footer_ok(path)
            if not ok:
                return False, f"mysql dump error: {msg}"

        return True, ""  # success


# ---------------------------------------------------------------------- #
# Helper


def _result(
    errors: List[str], warnings: List[str], metrics: Dict[str, Any]
) -> Dict[str, Any]:
    if errors:
        overall = "FAILED"
    elif warnings:
        overall = "WARN"
    else:
        overall = "PASSED"
    return {
        "overall": overall,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }
