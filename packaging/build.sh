#!/usr/bin/env bash
# Run this from the project root (the folder containing src/).
# Produces dist/AlarmClock — a single-file executable, no install needed.
set -e

cd "$(dirname "$0")/.."

pyinstaller --onefile --windowed --name AlarmClock \
    --add-data "src/resources:resources" \
    src/main.py

echo ""
echo "Build complete: dist/AlarmClock"
echo "Run it directly with: ./dist/AlarmClock"