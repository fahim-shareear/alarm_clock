# Alarm Clock

A custom desktop alarm clock for Ubuntu — dark cyberpunk UI with mint-green
glow accents, NTP-corrected time, automatic timezone detection, custom alarm
tones, and native `.deb` packaging. Built with Python + PySide6.

## Features

- Dark, glowing UI with a per-alarm customizable accent color
- 12h/24h clock format toggle, remembered across restarts
- NTP-corrected time (not just your system clock) with periodic re-sync
- Automatic timezone detection (OS setting, IP geolocation fallback)
- Per-alarm timezone selection — searchable dropdown, full IANA list
- 8 built-in alarm tones, plus the ability to import your own (`.mp3`/`.ogg`/`.wav`)
- One-time or repeat-by-weekday alarms
- Snooze (9 min) / Dismiss popup when an alarm fires, plus a desktop notification
- System tray integration — keeps running and firing alarms while minimized
- Add / Edit / Delete alarms — double-click to edit, right-click for a menu,
  Delete key, or a Delete button inside the edit dialog
- Installable as a real Ubuntu app via a `.deb` package, or run as a
  standalone binary

## Project structure

```
alarm_clock/
├── src/
│   ├── main.py                  # entry point
│   ├── core/
│   │   ├── models.py            # Alarm data model
│   │   ├── alarm_manager.py     # load/save alarms.json
│   │   ├── time_sync.py         # NTP correction + timezone auto-detect
│   │   ├── scheduler.py         # background alarm-firing checks
│   │   ├── audio_engine.py      # tone playback with fade-in
│   │   ├── notifier.py          # desktop notification helper
│   │   └── paths.py             # resource/user-data path resolution
│   ├── ui/
│   │   ├── main_window.py       # main window, tray, wiring
│   │   ├── alarm_dialog.py      # add/edit alarm dialog
│   │   ├── alarm_popup.py       # fired-alarm popup (snooze/dismiss)
│   │   └── widgets/
│   │       └── clock_face.py    # custom-painted glowing clock
│   └── resources/
│       ├── styles/theme.qss     # dark cyberpunk theme
│       └── tones/               # bundled default alarm tones
├── packaging/
│   ├── build.sh                 # PyInstaller -> dist/AlarmClock
│   ├── build_deb.sh             # wraps dist/AlarmClock into a .deb
│   ├── install.sh               # (legacy) manual launcher install
│   ├── alarm-clock.desktop      # launcher entry template
│   └── icon.png                 # app icon
└── requirements.txt
```

## Requirements

- Ubuntu 26.04 (or similar)
- Python 3.10+
- `dpkg-deb` (ships with Ubuntu by default) if you want to build a `.deb`

## Development setup

```bash
cd alarm_clock
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run it:

```bash
cd src
python main.py
```

> Always run `main.py` from inside `src/` — the `core` and `ui` packages are
> only importable relative to that entry point. Running a file inside
> `ui/` or `core/` directly (e.g. `python ui/alarm_dialog.py`) will fail
> with `ModuleNotFoundError`.

## Usage

- **Add Alarm** — set time, label, timezone, tone (built-in or your own via
  **Import…**), repeat days, and a glow color.
- **Edit** — double-click an alarm in the list.
- **Delete** — right-click an alarm → Delete, select it and press the
  Delete key, or open it for editing and click **Delete Alarm**.
- **12h / 24h** — toggle button next to "+ Add Alarm"; applies to the clock
  face, the alarm list, the time picker, and the fire popup.
- **Snooze / Dismiss** — shown when an alarm fires; Snooze reschedules for
  9 minutes later, Dismiss stops the tone immediately.
- **Tray icon** — minimizing or closing the window (the X button) hides it
  to tray rather than quitting, so alarms keep firing in the background.
  Right-click the tray icon → **Quit** to actually exit.
- **Your data** — alarms and imported tones are stored in
  `~/.local/share/alarm-clock/`, independent of wherever the app binary
  itself lives.

## Building a standalone executable

```bash
chmod +x packaging/build.sh
./packaging/build.sh
```

Produces `dist/AlarmClock` — a single-file executable. Run it directly with
`./dist/AlarmClock`.

## Building a `.deb` package

Run this *after* `build.sh` has produced `dist/AlarmClock`:

```bash
chmod +x packaging/build_deb.sh
./packaging/build_deb.sh
```

Produces `alarm-clock_1.0.0_amd64.deb` in the project root.

### Testing the `.deb` before installing

```bash
dpkg-deb -I alarm-clock_1.0.0_amd64.deb          # metadata
dpkg-deb -c alarm-clock_1.0.0_amd64.deb          # file listing
mkdir -p /tmp/alarm-clock-test
dpkg-deb -x alarm-clock_1.0.0_amd64.deb /tmp/alarm-clock-test
/tmp/alarm-clock-test/opt/alarm-clock/AlarmClock  # run it, exactly as installed
rm -rf /tmp/alarm-clock-test
```

### Installing

```bash
sudo apt install ./alarm-clock_1.0.0_amd64.deb
```

Installs the binary to `/opt/alarm-clock/`, the icon alongside it, and a
launcher entry to `/usr/share/applications/` — it'll show up in your app
launcher/dock with the mint-green clock icon.

### Uninstalling

```bash
sudo apt remove alarm-clock
```

This removes the installed binary and launcher entry only. Your saved
alarms and imported tones are untouched (they live outside the package, in
`~/.local/share/alarm-clock/`) — delete that folder too if you want a
completely clean removal:

```bash
rm -rf ~/.local/share/alarm-clock
```

## Alternative: launcher without a `.deb`

If you'd rather not build a `.deb`, `packaging/install.sh` copies the
`.desktop` launcher entry into `~/.local/share/applications/` pointing
straight at `dist/AlarmClock`, and can optionally set the app to autostart
on login (`~/.config/autostart/`):

```bash
chmod +x packaging/install.sh
./packaging/install.sh
```

> If you use both this and the `.deb` install, you may end up with a
> duplicate launcher entry — delete
> `~/.local/share/applications/alarm-clock.desktop` and keep the
> `.deb`-installed one at `/usr/share/applications/`.

## Troubleshooting

**`pyinstaller: command not found`**
Your virtual environment isn't active. Run `source venv/bin/activate` first
— your prompt should show `(venv)` when it's on.

**`Permission denied` running a `.sh` script**
Downloaded/copied scripts lose their executable bit:
`chmod +x packaging/build.sh packaging/install.sh packaging/build_deb.sh`

**`pygame`/SDL build errors during `pip install`**
This project uses `pygame-ce`, which ships pre-built wheels for common
platforms and shouldn't need to compile from source. If it still tries to
build from source, install the SDL2 dev headers:
```bash
sudo apt install pkg-config libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev libjpeg-dev python3-dev
```

**Ctrl+C doesn't stop the app in the terminal**
Fixed in `main.py` — it installs the default SIGINT handler and a small
idle timer so Python can actually catch the interrupt. If you're on an
older copy of `main.py` without that, Ctrl+C won't work reliably.

**The window's X button doesn't close the app**
This is intentional — closing the window hides it to the system tray so
scheduled alarms keep firing in the background. Use the tray icon's
**Quit** option to fully exit.

**No sound when an alarm fires**
Check the terminal for a `[warn] audio init failed` or
`[warn] could not load tone` message — usually means no tone was selected
in the alarm dialog, or the audio backend failed to initialize.

## Tech stack

PySide6 (Qt UI, painting, animations, tray) · ntplib (NTP sync) ·
tzdata / pytz / tzlocal (timezone handling) · requests (IP geolocation
fallback) · APScheduler (alarm-firing scheduler) · pygame-ce (audio
playback) · PyInstaller (packaging) · `dpkg-deb` (Debian packaging)