from datetime import datetime

from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QFont

ACCENT = QColor("#00E5A0")


class ClockFace(QWidget):
    """Large digital time display with a soft glow, ticking every second.

    Currently shows local system time. Once time_sync.py exists, swap the
    datetime.now() call for the NTP-corrected, timezone-aware time.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(160)

        # Soft glow around the widget itself
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(ACCENT)
        glow.setBlurRadius(40)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %d %B %Y")

        rect = self.rect()

        time_font = QFont("DejaVu Sans Mono", 48, QFont.Bold)
        painter.setFont(time_font)
        painter.setPen(ACCENT)
        painter.drawText(rect.adjusted(0, 0, 0, -30), Qt.AlignHCenter | Qt.AlignVCenter, time_str)

        date_font = QFont("DejaVu Sans", 12)
        painter.setFont(date_font)
        painter.setPen(QColor("#8FA3A0"))
        painter.drawText(rect.adjusted(0, 60, 0, 0), Qt.AlignHCenter | Qt.AlignTop, date_str)

        painter.end()