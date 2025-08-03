#!/usr/bin/env python3
"""
Persistent WatchDog daemon.

• Starts at system boot.
• Runs the Pulse workflow every day at 21:00:
      - all backups (serial)
      - (dummy) verification
      - Discord report

See docs/watchdog.service.template for the systemd unit.
"""

import time
from pathlib import Path

import schedule
from dotenv import load_dotenv

from watchdog.core.pulse import PulseService
from watchdog.core.status import StatusChecker

# --------------------------------------------------------------------------- #
# Environment

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

# --------------------------------------------------------------------------- #
# Scheduler helpers

def run_pulse() -> None:
    """Invoke Pulse once."""
    PulseService().run()

# --------------------------------------------------------------------------- #
# Main loop

def main() -> None:
    """Persistent scheduler loop."""
    print("WatchDog daemon started.")

    # Schedule Pulse once per day
    schedule.every().day.at("22:30").do(run_pulse)
    
    # StatusChecker (runs in background thread)
    cfg = ROOT_DIR / "watchdog" / "config" / "status_config.json"
    StatusChecker(cfg).start()

    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
