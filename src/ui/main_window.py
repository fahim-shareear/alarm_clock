from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QSystemTrayIcon, QMenu,
)
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon, QAction
from PySide6.QtCore import Qt

from ui.widgets.clock_face import ClockFace
from ui.alarm_dialog import AlarmDialog
from core.alarm_manager import AlarmManager

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

        self._build_ui()
        self._build_tray()
        self._refresh_alarm_list()

    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addWidget(ClockFace(self))

        header = QHBoxLayout()
        header.addWidget(QLabel("Alarms"))
        header.addStretch()
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

    def _quit(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    def _refresh_alarm_list(self) -> None:
        self.alarm_list.clear()
        for alarm in self.alarm_manager.all():
            days = ", ".join(d.capitalize() for d in sorted(alarm.repeat_days)) or "Once"
            label = f"{alarm.time.strftime('%H:%M')}  —  {alarm.label}  ({alarm.timezone}, {days})"
            if not alarm.enabled:
                label += "  [off]"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, alarm.id)
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

    def closeEvent(self, event) -> None:
        # Hide to tray instead of quitting, so scheduled alarms keep running
        event.ignore()
        self.hide()