#!/usr/bin/env bash
echo "Building FretTool executable with PyInstaller..."
echo ""

ICON_FLAG=""
if [ -f "icon.ico" ]; then
    ICON_FLAG="--icon=icon.ico"
elif [ -f "icon.icns" ]; then
    ICON_FLAG="--icon=icon.icns"
elif [ -f "icon.png" ]; then
    ICON_FLAG="--icon=icon.png"
else
    echo "Warning: no icon found (icon.ico, icon.icns, icon.png), building without icon"
fi

rm -rf build dist

# Use ; separator on Windows, : on Unix
pyinstaller --onefile --windowed --name=FretTool $ICON_FLAG --add-data "icon.ico;." main.py 2>/dev/null || \
    pyinstaller --onefile --windowed --name=FretTool $ICON_FLAG --add-data "icon.ico:." main.py

echo ""
if [ -f "dist/FretTool" ]; then
    echo "Build successful! Executable created at: dist/FretTool"
else
    echo "Build failed. Check the output above for errors."
fi
