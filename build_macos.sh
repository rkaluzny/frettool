#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "Error: This script is for macOS only. Current OS: $(uname -s)"
    exit 1
fi

APP_NAME="FretTool"
ICON="icon.icns"

if [ ! -f "$ICON" ]; then
    echo "Error: $ICON not found"
    exit 1
fi

echo "Building $APP_NAME macOS app bundle with PyInstaller..."
echo ""

rm -rf build dist

pyinstaller --onedir --windowed --name="$APP_NAME" \
    --icon="$ICON" \
    --add-data "icon.icns:." \
    --add-data "locales:locales" \
    main.py

echo ""
APP_BUNDLE="dist/$APP_NAME.app"
if [ -d "$APP_BUNDLE" ]; then
    echo "Build successful! App bundle created at: $APP_BUNDLE"

    # Remove quarantine attribute if present (downloaded files)
    xattr -dr com.apple.quarantine "$APP_BUNDLE" 2>/dev/null || true

    echo ""
    echo "To create a DMG, install create-dmg and run:"
    echo "  create-dmg --volname \"$APP_NAME\" --window-pos 200 120 --window-size 800 400 --icon-size 100 --icon \"$APP_NAME.app\" 200 190 --hide-extension \"$APP_NAME.app\" --app-drop-link 600 185 \"dist/$APP_NAME.dmg\" \"$APP_BUNDLE\""
else
    echo "Build failed. Check the output above for errors."
    exit 1
fi
