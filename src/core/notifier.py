from PySide6.QtWidgets import QSystemTrayIcon


def notify(tray: QSystemTrayIcon, title: str, message: str, msecs: int = 6000) -> None:
    """Native desktop notification via the tray icon — no extra
    dependency needed since QSystemTrayIcon already supports this."""
    if tray.supportsMessages():
        tray.showMessage(title, message, QSystemTrayIcon.Information, msecs)