from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import json

from watchdog.core.backup.backup_service import BackupService
from watchdog.core.backup.config_loader import BackupConfig
from watchdog.core.notify import DiscordNotifier
from watchdog.utils.logger import WatchdogLogger

from watchdog.core.verify.verifier_service import VerifierService


class PulseService:
    BACKUP_ROOT = Path("/mnt/ssd/backups")

    def __init__(self) -> None:
        self.logger = WatchdogLogger("pulse")
        cfg_path = Path(__file__).parents[2] / "config" / "backup_config.json"
        self.backup_cfg = BackupConfig(cfg_path)
        self.notifier = DiscordNotifier()

    # Public API

    def run(self) -> None:
        """Entry-point for daemon/CLI."""
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        try:
            self.logger.info("=== Pulse started ===")
            backup_ok = self._run_backups(ts)
            verify_ok, verify_data = self._run_verification(ts) if backup_ok else (False, {})
            self._send_report(ts, backup_ok, verify_ok, verify_data)
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Pulse failed: {exc}")
            self.notifier.send(content=f"❌ **Pulse {ts} failed:** ```{exc}```")

    # Internal helpers

    def _run_backups(self, timestamp: str) -> bool:
        """Run all backups serially; return True on success."""
        self.logger.info("Starting backups…")
        service = BackupService(self.backup_cfg)
        try:
            service.backup_all()  # existing logic is serial & blocking
            self.logger.info("All backups finished successfully.")
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Backup failure: {exc}")
            return False

    def _run_verification(self, timestamp: str) -> tuple[bool, Dict[str, Any]]:
        """Run verification on the newest backup set."""
        self.logger.info("Running verification…")
        backup_dir = self.BACKUP_ROOT / timestamp
        verifier = VerifierService()
        result = verifier.verify_pulse(backup_dir)
        ok = result["overall"] == "PASSED"
        return ok, result

    def _collect_backup_sizes(self, timestamp: str) -> Dict[str, Any]:
        """
        Scan /mnt/ssd/backups/<timestamp>/<server>/ and compute
        per-server size and file count, plus a grand total.
        """
        pulse_dir = self.BACKUP_ROOT / timestamp
        data: Dict[str, Any] = {"servers": [], "total_bytes": 0}

        if not pulse_dir.exists():
            return data

        for server_dir in sorted([p for p in pulse_dir.iterdir() if p.is_dir()]):
            bytes_sum = 0
            files = 0
            for f in server_dir.rglob("*"):
                if f.is_file():
                    try:
                        st = f.stat()
                        bytes_sum += st.st_size
                        files += 1
                    except OSError:
                        # skip unreadable entries
                        continue
            data["servers"].append(
                {"name": server_dir.name, "bytes": bytes_sum, "files": files}
            )
            data["total_bytes"] += bytes_sum

        # sort servers by size desc
        data["servers"].sort(key=lambda x: x["bytes"], reverse=True)
        return data

    @staticmethod
    def _human_bytes(num: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
        n = float(num)
        for u in units:
            if n < 1024.0:
                return f"{n:.2f} {u}"
            n /= 1024.0
        return f"{n:.2f} ZB"

    def _send_report(
        self,
        timestamp: str,
        backup_ok: bool,
        verify_ok: bool,
        verify_data: Dict[str, Any],
    ) -> None:
        """Compose and push the Discord embed."""
        status_backup = "✅ **Back-ups Success**" if backup_ok else "❌ **Back-ups Failed**"
        status_verify = "✅ **Verification Success**" if verify_ok else "⚠️ **Verification Failed**"

        # Build sizes field (safe even if backup failed; shows what exists)
        sizes = self._collect_backup_sizes(timestamp)
        if sizes["servers"]:
            lines = [f"**Total**: {self._human_bytes(sizes['total_bytes'])}"]
            for s in sizes["servers"]:
                lines.append(
                    f"- {s['name']}: {self._human_bytes(s['bytes'])} ({s['files']} files)"
                )
            sizes_text = "\n".join(lines)
            # Discord field hard limit ~1024 chars
            if len(sizes_text) > 1024:
                sizes_text = sizes_text[:1000] + "\n… (truncated)"
        else:
            sizes_text = "_No backup files found for this pulse._"

        embed = {
            "title": f"📊  WatchDog Pulse — {timestamp}",
            "color": 0x00FF00 if backup_ok and verify_ok else 0xFF0000,
            "fields": [
                {"name": "Back-ups", "value": status_backup, "inline": False},
                {
                    "name": "Verification",
                    "value": status_verify
                    + f"\nErrors: {len(verify_data.get('errors', []))} | "
                    + f"Warn: {len(verify_data.get('warnings', []))}",
                    "inline": False,
                },
                {"name": "Backup sizes", "value": sizes_text, "inline": False},
                {
                    "name": "Details (JSON)",
                    "value": f"```json\n{json.dumps(verify_data, indent=2)[:900]}```",
                    "inline": False,
                },
            ],
        }
        self.notifier.send(content="", embeds=[embed])
        self.logger.info("Pulse report sent to Discord.")
