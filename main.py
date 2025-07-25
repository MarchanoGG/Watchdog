#!/usr/bin/env python3
"""
WatchDog CLI entrypoint.

Usage:
    watchdog [backup|status|notify|all]
"""

import sys
import platform
import shutil
import datetime as dt
from pathlib import Path

import psutil
from dotenv import load_dotenv
from watchdog.core.notify import DiscordNotifier
from watchdog.core.pulse import PulseService
from watchdog.core.backup.backup_service import BackupService
from watchdog.core.backup.config_loader import BackupConfig

# Load environment variables from .env file if it exists
ENV_PATH = Path(__file__).parent / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)


def human_bytes(num: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} EB"


def generate_status_report() -> str:
    """Generate a basic system status report."""
    now = dt.datetime.now()
    uname = platform.uname()
    uptime_seconds = (dt.datetime.now() - dt.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    uptime_str = str(dt.timedelta(seconds=int(uptime_seconds)))

    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return (
        f"**WatchDog Status Report — {now:%Y-%m-%d %H:%M:%S}**\n"
        f"Host: `{uname.node}`\n"
        f"OS: {uname.system} {uname.release} ({uname.machine})\n"
        f"Uptime: {uptime_str}\n\n"
        f"**CPU**: {cpu_usage}%\n"
        f"**RAM**: {human_bytes(mem.used)} / {human_bytes(mem.total)} ({mem.percent}%)\n"
        f"**Disk** (/): {human_bytes(disk.used)} / {human_bytes(disk.total)} "
        f"({disk.used / disk.total * 100:.1f}%)"
    )


def run_pulse() -> None:
    PulseService().run()

def run_backup() -> None:
    try:
        config = BackupConfig(Path(__file__).parent / "watchdog/config/backup_config.json")
        backup_service = BackupService(config)
        backup_service.backup_all()
        print("[OK] Backup completed successfully.")
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")


def run_status() -> None:
    """Generate and print system status, then send it to Discord."""
    report = generate_status_report()
    print(report)

    try:
        DiscordNotifier().send(content=report)
        print("Status report successfully sent to Discord.")
    except Exception as exc:
        print(f"[ERROR] Failed to send to Discord: {exc}")


def run_notify() -> None:
    """Send a test notification to Discord."""
    try:
        DiscordNotifier().send(content="Test message: WatchDog notify test successful.")
        print("Test notification sent.")
    except Exception as exc:
        print(f"[ERROR] Failed to send to Discord: {exc}")


def show_help() -> None:
    """Show usage instructions."""
    print("Usage: watchdog [backup|status|notify|all]")


def main() -> None:
    """Main CLI dispatcher."""
    commands = {
        "backup": run_backup,
        "pulse": run_pulse,
        "notify": run_notify,
        "all": lambda: [run_backup(), run_pulse()],
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    commands.get(cmd, show_help)()


if __name__ == "__main__":
    main()
