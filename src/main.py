import sys
import os

from PySide6.QtWidgets import QApplication

# Make sibling packages (ui, core) importable regardless of where this is run from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow  # noqa: E402


def load_stylesheet(app: QApplication) -> None:
    theme_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "resources", "styles", "theme.qss",
    )
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

    sys.exit(app.exec())


if __name__ == "__main__":
    main()