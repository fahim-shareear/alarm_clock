from datetime import timedelta
from zoneinfo import ZoneInfo

from PySide6.QtCore import QObject, Signal
from apscheduler.schedulers.background import BackgroundScheduler

from core.alarm_manager import AlarmManager
from core.time_sync import TimeSync
from core.models import Alarm


class AlarmScheduler(QObject):
    """Polls alarms against NTP-corrected time and fires a Qt signal.

    Runs the actual checks on a background thread (APScheduler), but
    Signal emission across threads is queued by Qt automatically, so
    anything connected to alarm_fired runs safely on the GUI thread.
    """

    alarm_fired = Signal(object)  # emits an Alarm

    def __init__(self, alarm_manager: AlarmManager, time_sync: TimeSync, parent=None):
        super().__init__(parent)
        self.alarm_manager = alarm_manager
        self.time_sync = time_sync
        self._scheduler = BackgroundScheduler()
        self._fired_this_minute = set()   # "<alarm_id>:<YYYYMMDDHHMM>" dedupe keys
        self._snoozes = []                # [(fire_at_utc, Alarm), ...] — in-memory only

    def start(self) -> None:
        self.time_sync.sync_ntp()
        self._scheduler.add_job(self._check_alarms, "interval", seconds=15, id="alarm_check")
        self._scheduler.add_job(self._resync_time, "interval", minutes=30, id="time_resync")
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)

    def snooze(self, alarm: Alarm, minutes: int = 9) -> None:
        fire_at = self.time_sync.now_utc() + timedelta(minutes=minutes)
        self._snoozes.append((fire_at, alarm))

    def _resync_time(self) -> None:
        self.time_sync.sync_ntp()

    def _check_alarms(self) -> None:
        now_utc = self.time_sync.now_utc()

        # Snoozed alarms first
        still_pending = []
        for fire_at, alarm in self._snoozes:
            if now_utc >= fire_at:
                self.alarm_fired.emit(alarm)
            else:
                still_pending.append((fire_at, alarm))
        self._snoozes = still_pending

        # Regular scheduled alarms
        for alarm in self.alarm_manager.all():
            if not alarm.enabled:
                continue

            try:
                tz = ZoneInfo(alarm.timezone)
            except Exception:
                tz = ZoneInfo("UTC")
            local_now = now_utc.astimezone(tz)

            if local_now.hour != alarm.time.hour or local_now.minute != alarm.time.minute:
                continue

            if alarm.repeat_days:
                weekday_key = local_now.strftime("%a").lower()
                if weekday_key not in alarm.repeat_days:
                    continue

            fire_key = f"{alarm.id}:{local_now.strftime('%Y%m%d%H%M')}"
            if fire_key in self._fired_this_minute:
                continue
            self._fired_this_minute.add(fire_key)

            self.alarm_fired.emit(alarm)