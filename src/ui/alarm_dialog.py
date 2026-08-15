import os
import shutil
from datetime import time as dtime
from zoneinfo import available_timezones

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTimeEdit, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QDialogButtonBox, QFileDialog, QLabel, QWidget,
)
from PySide6.QtCore import QTime

from core.models import Alarm

TONES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "resources", "tones",
)
AUDIO_EXTENSIONS = (".mp3", ".ogg", ".wav")

DAY_KEYS = [("mon", "Mon"), ("tue", "Tue"), ("wed", "Wed"), ("thu", "Thu"),
            ("fri", "Fri"), ("sat", "Sat"), ("sun", "Sun")]

# A short, commonly-used list up front; full IANA list is searchable below it
COMMON_ZONES = [
    "UTC", "Asia/Dhaka", "Asia/Kolkata", "Asia/Dubai", "Asia/Singapore",
    "Asia/Tokyo", "Europe/London", "Europe/Berlin", "Europe/Paris",
    "America/New_York", "America/Chicago", "America/Los_Angeles",
    "Australia/Sydney",
]


class AlarmDialog(QDialog):
    """Modal dialog for creating or editing a single alarm.
    Call get_alarm() after exec() returns Accepted."""

    def __init__(self, parent=None, alarm: Alarm = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Alarm" if alarm else "Add Alarm")
        self.setMinimumWidth(360)
        self._editing_id = alarm.id if alarm else None

        self._build_ui()
        if alarm:
            self._populate_from(alarm)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.time_edit = QTimeEdit(QTime.currentTime())
        self.time_edit.setDisplayFormat("HH:mm")
        form.addRow("Time", self.time_edit)

        self.label_edit = QLineEdit("Alarm")
        form.addRow("Label", self.label_edit)

        self.timezone_combo = QComboBox()
        self.timezone_combo.setEditable(True)
        self.timezone_combo.setInsertPolicy(QComboBox.NoInsert)
        all_zones = sorted(available_timezones())
        # common zones first, then a separator, then everything else
        self.timezone_combo.addItems(COMMON_ZONES)
        self.timezone_combo.insertSeparator(len(COMMON_ZONES))
        self.timezone_combo.addItems(all_zones)
        self.timezone_combo.setCurrentText("Asia/Dhaka")
        form.addRow("Timezone", self.timezone_combo)

        tone_row = QWidget()
        tone_layout = QHBoxLayout(tone_row)
        tone_layout.setContentsMargins(0, 0, 0, 0)
        self.tone_combo = QComboBox()
        self._refresh_tones()
        browse_btn = QPushButton("Import…")
        browse_btn.clicked.connect(self._on_import_tone)
        tone_layout.addWidget(self.tone_combo, stretch=1)
        tone_layout.addWidget(browse_btn)
        form.addRow("Tone", tone_row)

        layout.addLayout(form)

        layout.addWidget(QLabel("Repeat"))
        days_row = QHBoxLayout()
        self.day_checks = {}
        for key, short in DAY_KEYS:
            cb = QCheckBox(short)
            self.day_checks[key] = cb
            days_row.addWidget(cb)
        layout.addLayout(days_row)

        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_tones(self) -> None:
        self.tone_combo.clear()
        os.makedirs(TONES_DIR, exist_ok=True)
        tones = sorted(
            f for f in os.listdir(TONES_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)
        )
        if not tones:
            self.tone_combo.addItem("(no tones yet — click Import…)")
            self.tone_combo.setEnabled(False)
        else:
            self.tone_combo.setEnabled(True)
            self.tone_combo.addItems(tones)

    def _on_import_tone(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an alarm tone", "",
            "Audio files (*.mp3 *.ogg *.wav)",
        )
        if not path:
            return
        os.makedirs(TONES_DIR, exist_ok=True)
        dest = os.path.join(TONES_DIR, os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(dest):
            shutil.copy2(path, dest)
        self._refresh_tones()
        self.tone_combo.setCurrentText(os.path.basename(dest))

    def _populate_from(self, alarm: Alarm) -> None:
        self.time_edit.setTime(QTime(alarm.time.hour, alarm.time.minute))
        self.label_edit.setText(alarm.label)
        self.timezone_combo.setCurrentText(alarm.timezone)
        if alarm.tone_path:
            self.tone_combo.setCurrentText(os.path.basename(alarm.tone_path))
        for key, cb in self.day_checks.items():
            cb.setChecked(key in alarm.repeat_days)
        self.enabled_check.setChecked(alarm.enabled)

    def get_alarm(self) -> Alarm:
        qt_time = self.time_edit.time()
        tone_name = self.tone_combo.currentText()
        tone_path = (
            os.path.join(TONES_DIR, tone_name)
            if self.tone_combo.isEnabled()
            else ""
        )
        repeat_days = {key for key, cb in self.day_checks.items() if cb.isChecked()}

        alarm = Alarm(
            time=dtime(qt_time.hour(), qt_time.minute()),
            timezone=self.timezone_combo.currentText().strip(),
            label=self.label_edit.text().strip() or "Alarm",
            tone_path=tone_path,
            repeat_days=repeat_days,
            enabled=self.enabled_check.isChecked(),
        )
        if self._editing_id:
            alarm.id = self._editing_id
        return alarm