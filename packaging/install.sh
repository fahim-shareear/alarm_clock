#!/usr/bin/env bash
# Run this after build.sh has produced dist/AlarmClock.
# Installs the app into the launcher, and optionally sets it to autostart.
set -e

cd "$(dirname "$0")"
DESKTOP_FILE="alarm-clock.desktop"

mkdir -p ~/.local/share/applications
cp "$DESKTOP_FILE" ~/.local/share/applications/
echo "Installed launcher entry: ~/.local/share/applications/$DESKTOP_FILE"

read -p "Also start Alarm Clock automatically on login? [y/N] " ans
if [[ "$ans" == "y" || "$ans" == "Y" ]]; then
    mkdir -p ~/.config/autostart
    cp "$DESKTOP_FILE" ~/.config/autostart/
    echo "Enabled autostart: ~/.config/autostart/$DESKTOP_FILE"
fi

echo ""
echo "Done. If the Exec path in $DESKTOP_FILE doesn't match where"
echo "dist/AlarmClock actually is on your machine, edit it before running this again."