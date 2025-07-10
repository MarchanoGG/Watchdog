#!/usr/bin/env python3
"""
WatchDog CLI-entrypoint.

Gebruik:
    watchdog [backup|status|notify|all]
"""

import sys
from pathlib import Path
import os
import platform
import shutil
import datetime as dt

from dotenv import load_dotenv
import psutil

ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# Lokale imports (pkg in dezelfde repo)
from notify.discord import DiscordNotifier 

# .env laden (staat in project-root)
ENV_PATH = Path(__file__).parent / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# ---------- helpers ---------------------------------------------------------


def human_bytes(num: int) -> str:
    """Converteer bytes naar leesbaar formaat."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} EB"


def generate_status_report() -> str:
    """Maak een simpel statusrapport van de host."""
    now = dt.datetime.now()
    uname = platform.uname()
    uptime_seconds = (dt.datetime.now() - dt.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    uptime_str = str(dt.timedelta(seconds=int(uptime_seconds)))

    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    report = (
        f"**WatchDog Statusrapport — {now:%Y-%m-%d %H:%M:%S}**\n"
        f"Host: `{uname.node}`  \n"
        f"OS: {uname.system} {uname.release} ({uname.machine})  \n"
        f"Uptime: {uptime_str}  \n\n"
        f"**CPU**: {cpu_usage}%  \n"
        f"**RAM**: {human_bytes(mem.used)} / {human_bytes(mem.total)} "
        f"({mem.percent}%)  \n"
        f"**Disk** (/): {human_bytes(disk.used)} / {human_bytes(disk.total)} "
        f"({disk.percent}%)"
    )
    return report


# ---------- CLI -------------------------------------------------------------


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"

    if command == "backup":
        print("Backup-service nog niet geïmplementeerd.")
        # TODO: BackupService().run_backup()
    elif command == "status":
        report = generate_status_report()
        print(report)  # Toon lokaal

        try:
            notifier = DiscordNotifier()
            notifier.send(content=report)
            print("Statusrapport succesvol naar Discord gestuurd.")
        except Exception as exc:  # noqa: BLE001
            print(f"Fout bij verzenden naar Discord: {exc}")
    elif command == "notify":
        try:
            notifier = DiscordNotifier()
            notifier.send(content="Testbericht: WatchDog notify-test geslaagd.")
            print("Testnotificatie verstuurd.")
        except Exception as exc:  # noqa: BLE001
            print(f"Fout bij verzenden naar Discord: {exc}")
    else:
        print("Gebruik: watchdog [backup|status|notify|all]")


if __name__ == "__main__":
    main()
