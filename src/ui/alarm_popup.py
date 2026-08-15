from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSettings

from core.models import Alarm


class AlarmPopup(QDialog):
    """Shown when an alarm fires. Stays on top; caller wires the
    snooze/dismiss callbacks (typically stopping audio + rescheduling)."""

    def __init__(self, alarm: Alarm, on_snooze, on_dismiss, parent=None):
        super().__init__(parent)
        self.alarm = alarm
        self._on_snooze = on_snooze
        self._on_dismiss = on_dismiss

        self.setWindowTitle("Alarm")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)

        use_12h = QSettings("ArcticShark", "AlarmClock").value("use_12h", False, type=bool)
        time_str = alarm.time.strftime("%I:%M %p") if use_12h else alarm.time.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setAlignment(Qt.AlignCenter)
        time_label.setStyleSheet(
            f"font-size: 42px; font-weight: bold; color: {alarm.accent_color};"
        )
        layout.addWidget(time_label)

        title_label = QLabel(alarm.label)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(title_label)

        btn_row = QHBoxLayout()
        snooze_btn = QPushButton("Snooze 9 min")
        snooze_btn.clicked.connect(self._snooze_clicked)
        dismiss_btn = QPushButton("Dismiss")
        dismiss_btn.clicked.connect(self._dismiss_clicked)
        btn_row.addWidget(snooze_btn)
        btn_row.addWidget(dismiss_btn)
        layout.addLayout(btn_row)

    def _snooze_clicked(self) -> None:
        self._on_snooze(self.alarm)
        self.accept()

    def _dismiss_clicked(self) -> None:
        self._on_dismiss(self.alarm)
        self.accept()

    def closeEvent(self, event) -> None:
        # Treat the window-close (X) button as a dismiss, not a silent skip
        self._on_dismiss(self.alarm)
        event.accept()