from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from watchdog.core.backup.backup_service import BackupService
from watchdog.core.backup.config_loader import BackupConfig
from watchdog.core.notify import DiscordNotifier
from watchdog.utils.logger import WatchdogLogger

from .dummy_verifier import DummyVerifier


class PulseService:
    BACKUP_ROOT = Path("/mnt/ssd/backups")

    def __init__(self) -> None:
        self.logger = WatchdogLogger("pulse")
        cfg_path = Path(__file__).parents[2] / "config" / "backup_config.json"
        self.backup_cfg = BackupConfig(cfg_path)
        self.notifier = DiscordNotifier()

    # Public API ---------------------------------------------------------

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

    # Internal helpers ---------------------------------------------------

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
        """Run (dummy) verification on the newest backup set."""
        self.logger.info("Running dummy verification…")
        backup_dir = self.BACKUP_ROOT / timestamp
        verifier = DummyVerifier()
        result = verifier.verify(backup_dir)
        ok = result.get("overall") == "PASSED"
        self.logger.info(f"Verification result: {result}")
        return ok, result

    def _send_report(
        self,
        timestamp: str,
        backup_ok: bool,
        verify_ok: bool,
        verify_data: Dict[str, Any],
    ) -> None:
        """Compose and push the Discord embed."""
        status_backup = "✅ **Back-ups Success**" if backup_ok else "❌ **Back-ups Failed**"
        status_verify = (
            "✅ **Verification Success**" if verify_ok else "⚠️ **Verification Failed**"
        )

        embed = {
            "title": f"📊  WatchDog Pulse — {timestamp}",
            "color": 0x00FF00 if backup_ok and verify_ok else 0xFF0000,
            "fields": [
                {"name": "Back-ups", "value": status_backup, "inline": False},
                {"name": "Verification", "value": status_verify, "inline": False},
                {
                    "name": "Details (dummy)",
                    "value": f"```json\n{verify_data}```"[:1024],
                    "inline": False,
                },
            ],
        }
        self.notifier.send(content="", embeds=[embed])
        self.logger.info("Pulse report sent to Discord.")
