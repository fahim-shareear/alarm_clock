#!/usr/bin/env bash
# Run this AFTER build.sh has already produced dist/AlarmClock.
# Produces alarm-clock_1.0.0_amd64.deb in the project root.
set -e

cd "$(dirname "$0")/.."   # project root

if [ ! -f "dist/AlarmClock" ]; then
    echo "dist/AlarmClock not found — run ./packaging/build.sh first."
    exit 1
fi

PKG_NAME="alarm-clock"
VERSION="1.0.0"
ARCH="amd64"
STAGE="packaging/deb-stage"

rm -rf "$STAGE"

# Debian package metadata
mkdir -p "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" << EOF
Package: $PKG_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Fahim Shareear <you@example.com>
Description: Custom alarm clock with international timezone sync
 A desktop alarm clock with a custom dark UI, NTP time sync,
 automatic timezone detection, and custom alarm tones.
EOF

# The app binary — installed under /opt since it's a self-contained
# PyInstaller bundle, not a system-managed executable
mkdir -p "$STAGE/opt/alarm-clock"
cp dist/AlarmClock "$STAGE/opt/alarm-clock/AlarmClock"
cp packaging/icon.png "$STAGE/opt/alarm-clock/icon.png"
chmod 755 "$STAGE/opt/alarm-clock/AlarmClock"

# Desktop launcher entry, pointing at the installed /opt location
mkdir -p "$STAGE/usr/share/applications"
cat > "$STAGE/usr/share/applications/alarm-clock.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Alarm Clock
Comment=Custom alarm clock with international timezone sync
Exec=/opt/alarm-clock/AlarmClock
Icon=/opt/alarm-clock/icon.png
Terminal=false
Categories=Utility;Clock;
StartupWMClass=AlarmClock
EOF

# Build the .deb — root-owner-group avoids needing sudo for file ownership
dpkg-deb --build --root-owner-group "$STAGE" "${PKG_NAME}_${VERSION}_${ARCH}.deb"

rm -rf "$STAGE"

echo ""
echo "Built: ${PKG_NAME}_${VERSION}_${ARCH}.deb"
echo "Install it with: sudo apt install ./${PKG_NAME}_${VERSION}_${ARCH}.deb"