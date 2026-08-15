from datetime import datetime

from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QFont

ACCENT = QColor("#00E5A0")


class ClockFace(QWidget):
    """Large digital time display with a soft glow, ticking every second.

    Currently shows local system time. Once time_sync.py's NTP-corrected
    time is wired in, swap the datetime.now() call for that.
    """

    DATE_ZONE_HEIGHT = 34  # fixed strip at the bottom, so it never overlaps the time text

    def __init__(self, parent=None, use_12h: bool = False):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.use_12h = use_12h

        # Soft glow around the widget itself
        glow = QGraphicsDropShadowEffect(self)
        glow.setColor(ACCENT)
        glow.setBlurRadius(40)
        glow.setOffset(0, 0)
        self.setGraphicsEffect(glow)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(1000)

    def set_12h(self, enabled: bool) -> None:
        self.use_12h = enabled
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p") if self.use_12h else now.strftime("%H:%M:%S")
        date_str = now.strftime("%A, %d %B %Y")

        full_rect = self.rect()
        date_zone = QRect(
            full_rect.left(), full_rect.bottom() - self.DATE_ZONE_HEIGHT,
            full_rect.width(), self.DATE_ZONE_HEIGHT,
        )
        time_zone = QRect(
            full_rect.left(), full_rect.top(),
            full_rect.width(), full_rect.height() - self.DATE_ZONE_HEIGHT,
        )

        time_font = QFont("DejaVu Sans Mono", 44, QFont.Bold)
        painter.setFont(time_font)
        painter.setPen(ACCENT)
        painter.drawText(time_zone, Qt.AlignHCenter | Qt.AlignVCenter, time_str)

        date_font = QFont("DejaVu Sans", 12)
        painter.setFont(date_font)
        painter.setPen(QColor("#8FA3A0"))
        painter.drawText(date_zone, Qt.AlignHCenter | Qt.AlignVCenter, date_str)

        painter.end()