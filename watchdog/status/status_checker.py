"""
StatusChecker
- Polls targets on a fixed interval.
- Only notifies Discord on state-changes (UP ➜ DOWN  or  DOWN ➜ UP).
"""

from __future__ import annotations
import socket, time, requests, threading
from pathlib import Path
from typing import Dict, Any, List

from watchdog.utils.logger import WatchdogLogger
from watchdog.core.notify import DiscordNotifier
import json

class StatusChecker:
    def __init__(self, cfg_path: Path) -> None:
        self.cfg_path = cfg_path
        self.load_cfg()
        self.logger   = WatchdogLogger("status")
        self.notifier = DiscordNotifier()
        # remember previous state to avoid spam
        self.state: Dict[str, bool] = {t["name"]: True for t in self.targets}

    def load_cfg(self) -> None:
        data = json.loads(Path(self.cfg_path).read_text())
        self.interval = max(5, data.get("interval_sec", 30))
        self.timeout  = max(1, data.get("timeout_sec", 5))
        self.targets  = data["targets"]

    def start(self) -> None:
        """Kick-off in its own thread (non-blocking)."""
        th = threading.Thread(target=self._loop, daemon=True)
        th.start()

    def _loop(self) -> None:
        while True:
            self.load_cfg()                      # hot-reload config
            for t in self.targets:
                ok = self._check_target(t)
                prev = self.state.get(t["name"], True)
                if ok != prev:                   # state change? → notify
                    self._notify(t, ok)
                    self.state[t["name"]] = ok
            time.sleep(self.interval)

    # single checks
    def _check_target(self, t: Dict[str, Any]) -> bool:
        try:
            if t["method"] in ("http", "https"):
                r = requests.get(t["url"], timeout=self.timeout)
                return r.status_code < 500
            if t["method"] == "tcp":
                with socket.create_connection(
                    (t["host"], t["port"]), timeout=self.timeout
                ):
                    return True
        except Exception as exc:
            self.logger.warning(f"{t['name']} check error: {exc}")
        return False

    # Discord push
    def _notify(self, t: Dict[str, Any], ok: bool) -> None:
        status = "🟢 UP again" if ok else "🔴 DOWN"
        msg = f"**{t['name']}** {status}"
        self.notifier.send(content=msg)
        self.logger.info(f"Notified: {msg}")
