import json
import os
from typing import List

from core.models import Alarm
from core.paths import user_data_dir

DATA_FILE = os.path.join(user_data_dir(), "alarms.json")


class AlarmManager:
    """In-memory alarm list backed by a JSON file on disk."""

    def __init__(self):
        self.alarms: List[Alarm] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(DATA_FILE):
            self.alarms = []
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.alarms = [Alarm.from_dict(item) for item in raw]
        except (json.JSONDecodeError, KeyError, ValueError):
            print(f"[warn] could not parse {DATA_FILE}, starting with no alarms")
            self.alarms = []

    def _save(self) -> None:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in self.alarms], f, indent=2)

    def add(self, alarm: Alarm) -> None:
        self.alarms.append(alarm)
        self._save()

    def remove(self, alarm_id: str) -> None:
        self.alarms = [a for a in self.alarms if a.id != alarm_id]
        self._save()

    def update(self, alarm: Alarm) -> None:
        for i, a in enumerate(self.alarms):
            if a.id == alarm.id:
                self.alarms[i] = alarm
                break
        self._save()

    def set_enabled(self, alarm_id: str, enabled: bool) -> None:
        for a in self.alarms:
            if a.id == alarm_id:
                a.enabled = enabled
                break
        self._save()

    def all(self) -> List[Alarm]:
        return list(self.alarms)