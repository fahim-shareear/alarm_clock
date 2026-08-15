import os
import sys


def resource_path(*parts) -> str:
    """Path to a bundled, read-only resource (theme, any bundled tones).
    Works both running from source and frozen via PyInstaller --onefile,
    where files are extracted to a temporary sys._MEIPASS directory."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/
    return os.path.join(base, "resources", *parts)


def user_data_dir() -> str:
    """Writable per-user directory for alarms.json etc. Never inside the
    frozen bundle — that location is read-only/temporary at runtime."""
    base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    path = os.path.join(base, "alarm-clock")
    os.makedirs(path, exist_ok=True)
    return path


def user_tones_dir() -> str:
    path = os.path.join(user_data_dir(), "tones")
    os.makedirs(path, exist_ok=True)
    return path