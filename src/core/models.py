from dataclasses import dataclass, field
from datetime import time
import uuid


@dataclass
class Alarm:
    """A single alarm entry."""

    time: time                          # local wall-clock time the alarm fires
    timezone: str = "UTC"               # IANA zone name, e.g. "Asia/Dhaka"
    label: str = "Alarm"
    tone_path: str = ""                 # path to the sound file to play
    repeat_days: set = field(default_factory=set)  # {"mon","tue",...} — empty = one-time
    enabled: bool = True
    accent_color: str = "#00E5A0"       # mint green glow color for this alarm's card
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time.strftime("%H:%M"),
            "timezone": self.timezone,
            "label": self.label,
            "tone_path": self.tone_path,
            "repeat_days": sorted(self.repeat_days),
            "enabled": self.enabled,
            "accent_color": self.accent_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Alarm":
        hh, mm = map(int, data["time"].split(":"))
        return cls(
            time=time(hh, mm),
            timezone=data.get("timezone", "UTC"),
            label=data.get("label", "Alarm"),
            tone_path=data.get("tone_path", ""),
            repeat_days=set(data.get("repeat_days", [])),
            enabled=data.get("enabled", True),
            accent_color=data.get("accent_color", "#00E5A0"),
            id=data.get("id", str(uuid.uuid4())),
        )