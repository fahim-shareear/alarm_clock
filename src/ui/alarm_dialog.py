import os
import shutil
from datetime import time as dtime
from zoneinfo import available_timezones

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTimeEdit, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QDialogButtonBox, QFileDialog, QLabel, QWidget, QColorDialog,
)
from PySide6.QtCore import QTime, QSettings
from PySide6.QtGui import QColor

from core.models import Alarm
from core.paths import user_tones_dir, resource_path

USER_TONES_DIR = user_tones_dir()
BUNDLED_TONES_DIR = resource_path("tones")
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
        elif self._tone_paths:
            self.tone_combo.setCurrentIndex(0)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.time_edit = QTimeEdit(QTime.currentTime())
        use_12h = QSettings("ArcticShark", "AlarmClock").value("use_12h", False, type=bool)
        self.time_edit.setDisplayFormat("hh:mm AP" if use_12h else "HH:mm")
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

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Glow color"))
        self._accent_color = "#00E5A0"
        self.color_btn = QPushButton()
        self.color_btn.setFixedWidth(50)
        self._update_color_btn()
        self.color_btn.clicked.connect(self._on_pick_color)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()
        layout.addLayout(color_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_tones(self) -> None:
        """Rebuilds the tone dropdown from bundled defaults + user imports.
        self._tone_paths maps the visible label -> real file path, since
        bundled and imported tones live in different directories."""
        self.tone_combo.clear()
        self._tone_paths = {}

        if os.path.isdir(BUNDLED_TONES_DIR):
            bundled = sorted(
                f for f in os.listdir(BUNDLED_TONES_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)
            )
            for f in bundled:
                name = os.path.splitext(f)[0]
                self._tone_paths[f"{name}  (built-in)"] = os.path.join(BUNDLED_TONES_DIR, f)

        os.makedirs(USER_TONES_DIR, exist_ok=True)
        imported = sorted(
            f for f in os.listdir(USER_TONES_DIR) if f.lower().endswith(AUDIO_EXTENSIONS)
        )
        for f in imported:
            self._tone_paths[f] = os.path.join(USER_TONES_DIR, f)

        if not self._tone_paths:
            self.tone_combo.addItem("(no tones yet — click Import…)")
            self.tone_combo.setEnabled(False)
        else:
            self.tone_combo.setEnabled(True)
            self.tone_combo.addItems(list(self._tone_paths.keys()))

    def _on_import_tone(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose an alarm tone", "",
            "Audio files (*.mp3 *.ogg *.wav)",
        )
        if not path:
            return
        os.makedirs(USER_TONES_DIR, exist_ok=True)
        dest = os.path.join(USER_TONES_DIR, os.path.basename(path))
        if os.path.abspath(path) != os.path.abspath(dest):
            shutil.copy2(path, dest)
        self._refresh_tones()
        self.tone_combo.setCurrentText(os.path.basename(dest))

    def _update_color_btn(self) -> None:
        self.color_btn.setStyleSheet(
            f"background-color: {self._accent_color}; border-radius: 4px; border: none;"
        )

    def _on_pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._accent_color), self, "Pick glow color")
        if color.isValid():
            self._accent_color = color.name()
            self._update_color_btn()

    def _populate_from(self, alarm: Alarm) -> None:
        self.time_edit.setTime(QTime(alarm.time.hour, alarm.time.minute))
        self.label_edit.setText(alarm.label)
        self.timezone_combo.setCurrentText(alarm.timezone)
        if alarm.tone_path:
            match = next(
                (label for label, path in self._tone_paths.items() if path == alarm.tone_path),
                None,
            )
            if match:
                self.tone_combo.setCurrentText(match)
        for key, cb in self.day_checks.items():
            cb.setChecked(key in alarm.repeat_days)
        self.enabled_check.setChecked(alarm.enabled)
        self._accent_color = alarm.accent_color
        self._update_color_btn()

    def get_alarm(self) -> Alarm:
        qt_time = self.time_edit.time()
        tone_label = self.tone_combo.currentText()
        tone_path = (
            self._tone_paths.get(tone_label, "")
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
            accent_color=self._accent_color,
        )
        if self._editing_id:
            alarm.id = self._editing_id
        return alarm