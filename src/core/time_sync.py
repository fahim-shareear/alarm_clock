from datetime import datetime, timezone

import ntplib
import requests
import tzlocal

NTP_SERVERS = ["pool.ntp.org", "time.google.com", "time.cloudflare.com"]
IP_GEOLOCATION_URL = "https://ipapi.co/json/"


class TimeSync:
    """Keeps an NTP-corrected offset from the system clock, and can
    auto-detect the user's current IANA timezone."""

    def __init__(self):
        self._offset_seconds = 0.0
        self.last_sync_ok = False

    def sync_ntp(self) -> bool:
        client = ntplib.NTPClient()
        for server in NTP_SERVERS:
            try:
                response = client.request(server, version=3, timeout=3)
                self._offset_seconds = response.offset
                self.last_sync_ok = True
                return True
            except Exception:
                continue
        self.last_sync_ok = False
        return False

    def now_utc(self) -> datetime:
        """Current UTC time, corrected by the last successful NTP offset."""
        corrected_ts = datetime.now(timezone.utc).timestamp() + self._offset_seconds
        return datetime.fromtimestamp(corrected_ts, tz=timezone.utc)

    def detect_timezone(self) -> str:
        """Best-effort current IANA timezone name.
        Tries the OS setting first (fast, no network), falls back to
        IP geolocation (handles the 'traveling, OS zone stale' case)."""
        try:
            name = tzlocal.get_localzone_name()
            if name:
                return name
        except Exception:
            pass

        try:
            resp = requests.get(IP_GEOLOCATION_URL, timeout=3)
            data = resp.json()
            name = data.get("timezone")
            if name:
                return name
        except Exception:
            pass

        return "UTC"