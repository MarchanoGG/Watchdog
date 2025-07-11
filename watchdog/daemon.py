#!/usr/bin/env python3
"""
Persistent WatchDog daemon.
Sends a full system status report to Discord every 3 hours.

Run stand-alone or via systemd (see docs/watchdog.service.template).
"""

import time
import datetime as dt
import platform
import shutil
from pathlib import Path

import psutil
import schedule
from dotenv import load_dotenv

from watchdog.core.notify import DiscordNotifier

# --------------------------------------------------------------------------- #
# Environment

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# --------------------------------------------------------------------------- #
# Helpers

def human_bytes(num: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} EB"

def generate_status_report() -> str:
    """Return a Markdown-formatted system status report."""
    now = dt.datetime.now()
    uname = platform.uname()
    uptime_seconds = (dt.datetime.now() - dt.datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    uptime_str = str(dt.timedelta(seconds=int(uptime_seconds)))

    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage("/")

    return (
        f"**WatchDog Status Report - {now:%Y-%m-%d %H:%M:%S}**\n"
        f"Host: `{uname.node}`\n"
        f"OS: {uname.system} {uname.release} ({uname.machine})\n"
        f"Uptime: {uptime_str}\n\n"
        f"**CPU**: {cpu_usage}%\n"
        f"**RAM**: {human_bytes(mem.used)} / {human_bytes(mem.total)} ({mem.percent}%)\n"
        f"**Disk** (/): {human_bytes(disk.used)} / {human_bytes(disk.total)} "
        f"({disk.used / disk.total * 100:.1f}%)"
    )

# --------------------------------------------------------------------------- #
# Main daemon logic

def push_status_to_discord() -> None:
    """Generate a report and send it to Discord."""
    report = generate_status_report()
    try:
        DiscordNotifier().send(content=report)
        print(f"[{dt.datetime.now()}] Status pushed to Discord")
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Discord push failed: {exc}")

def main() -> None:
    """Persistent scheduler loop."""
    print("WatchDog daemon started. Sending status every 3 hours.")
    # First push immediately on startup
    push_status_to_discord()

    # Every 3 hours afterwards
    schedule.every(3).hours.do(push_status_to_discord)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
