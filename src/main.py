import sys
import os
import signal

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Make sibling packages (ui, core) importable regardless of where this is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow  # noqa: E402
from core.paths import resource_path  # noqa: E402


def load_stylesheet(app: QApplication) -> None:
    theme_path = resource_path("styles", "theme.qss")
    try:
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print(f"[warn] theme file not found at {theme_path}, using default Qt style")


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Alarm Clock")

    # Don't quit when the window is closed — the tray icon keeps the app alive
    # so scheduled alarms still fire in the background.
    app.setQuitOnLastWindowClosed(False)

    load_stylesheet(app)

    window = MainWindow()
    window.show()

    # Qt's C++ event loop doesn't check for Python signals (like Ctrl+C)
    # on its own, so KeyboardInterrupt never gets a chance to fire. Restore
    # the default SIGINT handler and give the interpreter a periodic gap
    # (via a no-op timer) to actually notice the signal.
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    interrupt_timer = QTimer()
    interrupt_timer.timeout.connect(lambda: None)
    interrupt_timer.start(200)

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        print("\nInterrupted — shutting down.")
        window.scheduler.stop()
        exit_code = 0

    sys.exit(exit_code)


if __name__ == "__main__":
    main()