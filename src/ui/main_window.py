from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QSystemTrayIcon, QMenu,
)
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon, QAction
from PySide6.QtCore import Qt, QSettings

from ui.widgets.clock_face import ClockFace
from ui.alarm_dialog import AlarmDialog
from ui.alarm_popup import AlarmPopup
from core.alarm_manager import AlarmManager
from core.time_sync import TimeSync
from core.scheduler import AlarmScheduler
from core.audio_engine import AudioEngine
from core.notifier import notify
from core.models import Alarm

ACCENT = "#00E5A0"


def make_tray_icon() -> QIcon:
    """Draws a simple filled circle as a placeholder tray icon.
    Swap this for a real .png/.svg asset later."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(ACCENT))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(8, 8, 48, 48)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alarm Clock")
        self.resize(420, 560)

        self.alarm_manager = AlarmManager()
        self.time_sync = TimeSync()
        self.audio_engine = AudioEngine()
        self.scheduler = AlarmScheduler(self.alarm_manager, self.time_sync, self)
        self.settings = QSettings("ArcticShark", "AlarmClock")

        self._active_popup = None  # keeps a currently-firing popup alive

        self._build_ui()
        self._build_tray()
        self._refresh_alarm_list()

        self.scheduler.alarm_fired.connect(self._on_alarm_fired)
        self.scheduler.start()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addWidget(ClockFace(self))
        self.clock_face = layout.itemAt(0).widget()
        self.use_12h = self.settings.value("use_12h", False, type=bool)
        self.clock_face.set_12h(self.use_12h)

        header = QHBoxLayout()
        header.addWidget(QLabel("Alarms"))
        header.addStretch()
        self.format_btn = QPushButton("12h" if not self.use_12h else "24h")
        self.format_btn.setToolTip("Switch clock display format")
        self.format_btn.clicked.connect(self._on_toggle_format)
        header.addWidget(self.format_btn)
        add_btn = QPushButton("+ Add Alarm")
        add_btn.clicked.connect(self._on_add_alarm_clicked)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.alarm_list = QListWidget(self)
        self.alarm_list.itemDoubleClicked.connect(self._on_alarm_double_clicked)
        layout.addWidget(self.alarm_list, stretch=1)

        self.setCentralWidget(central)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(make_tray_icon(), self)
        self.tray.setToolTip("Alarm Clock")

        menu = QMenu()
        show_action = QAction("Open", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(show_action)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()
            self.activateWindow()

    def _on_toggle_format(self) -> None:
        self.use_12h = not self.use_12h
        self.clock_face.set_12h(self.use_12h)
        self.format_btn.setText("24h" if self.use_12h else "12h")
        self.settings.setValue("use_12h", self.use_12h)
        self._refresh_alarm_list()

    def _quit(self) -> None:
        from PySide6.QtWidgets import QApplication
        self.scheduler.stop()
        QApplication.quit()

    def _refresh_alarm_list(self) -> None:
        self.alarm_list.clear()
        for alarm in self.alarm_manager.all():
            days = ", ".join(d.capitalize() for d in sorted(alarm.repeat_days)) or "Once"
            time_str = alarm.time.strftime("%I:%M %p") if self.use_12h else alarm.time.strftime("%H:%M")
            label = f"{time_str}  —  {alarm.label}  ({alarm.timezone}, {days})"
            if not alarm.enabled:
                label += "  [off]"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, alarm.id)
            item.setForeground(QColor(alarm.accent_color))
            self.alarm_list.addItem(item)

    def _on_add_alarm_clicked(self) -> None:
        dialog = AlarmDialog(self)
        if dialog.exec() == AlarmDialog.Accepted:
            new_alarm = dialog.get_alarm()
            self.alarm_manager.add(new_alarm)
            self._refresh_alarm_list()

    def _on_alarm_double_clicked(self, item: QListWidgetItem) -> None:
        alarm_id = item.data(Qt.UserRole)
        alarm = next((a for a in self.alarm_manager.all() if a.id == alarm_id), None)
        if alarm is None:
            return
        dialog = AlarmDialog(self, alarm=alarm)
        if dialog.exec() == AlarmDialog.Accepted:
            self.alarm_manager.update(dialog.get_alarm())
            self._refresh_alarm_list()

    def _on_alarm_fired(self, alarm: Alarm) -> None:
        self.audio_engine.play(alarm.tone_path, loop=True)
        notify(self.tray, "Alarm", alarm.label)

        self._active_popup = AlarmPopup(
            alarm,
            on_snooze=self._handle_snooze,
            on_dismiss=self._handle_dismiss,
            parent=self,
        )
        self._active_popup.show()
        self._active_popup.raise_()
        self._active_popup.activateWindow()

        # One-time alarms turn themselves off once they've fired
        if not alarm.repeat_days:
            self.alarm_manager.set_enabled(alarm.id, False)
            self._refresh_alarm_list()

    def _handle_snooze(self, alarm: Alarm) -> None:
        self.audio_engine.stop()
        self.scheduler.snooze(alarm, minutes=9)

    def _handle_dismiss(self, alarm: Alarm) -> None:
        self.audio_engine.stop()

    def closeEvent(self, event) -> None:
        # Hide to tray instead of quitting, so scheduled alarms keep running
        event.ignore()
        self.hide()