import logging
from pathlib import Path

class WatchdogLogger:
    def __init__(self, name: str):
        log_dir = Path(f"/opt/watchdog/logs/")
        log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_dir / f"{name}.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not self.logger.hasHandlers():
            self.logger.addHandler(handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)
