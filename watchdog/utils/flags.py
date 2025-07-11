"""Helper functions for simple lock and flag files in /tmp/watchdog."""
from pathlib import Path

TMP_DIR = Path("/tmp/watchdog")
TMP_DIR.mkdir(parents=True, exist_ok=True)

def _file(name: str) -> Path:
    return TMP_DIR / f"{name}.flag"

def set_flag(name: str) -> None:
    _file(name).touch()

def clear_flag(name: str) -> None:
    f = _file(name)
    if f.exists():
        f.unlink()

def is_flag_set(name: str) -> bool:
    return _file(name).exists()
