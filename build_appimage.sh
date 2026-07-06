#!/usr/bin/env bash
# Build a FretTool AppImage for Linux
# Run this script on Linux after building the PyInstaller binary.
set -euo pipefail

APP_NAME="FretTool"
APP_DIR="${APP_NAME}.AppDir"
OUTPUT="${APP_NAME}-x86_64.AppImage"

echo "==> Building AppImage for ${APP_NAME}"

# Clean previous build
rm -rf "$APP_DIR" "$OUTPUT"

# Build PyInstaller binary first if missing
if [ ! -f "dist/${APP_NAME}" ]; then
    echo "==> dist/${APP_NAME} not found. Running build.sh..."
    if [ -f "build.sh" ]; then
        bash build.sh
    else
        pyinstaller --onefile --windowed --name="${APP_NAME}" \
            --add-data "locales:locales" main.py
    fi
fi

if [ ! -f "dist/${APP_NAME}" ]; then
    echo "Error: dist/${APP_NAME} not found after build."
    exit 1
fi

# Create AppDir structure
echo "==> Creating AppDir structure..."
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
for size in 256 128 64 48 32; do
    mkdir -p "${APP_DIR}/usr/share/icons/hicolor/${size}x${size}/apps"
done

# Copy binary
cp "dist/${APP_NAME}" "${APP_DIR}/usr/bin/"

# Create .desktop file
cat > "${APP_DIR}/usr/share/applications/frettool.desktop" << EOF
[Desktop Entry]
Name=${APP_NAME}
Comment=Professional Guitar Fretboard Designer
Exec=usr/bin/${APP_NAME}
Icon=frettool
Terminal=false
Type=Application
Categories=Audio;Education;
StartupNotify=true
EOF

cp "${APP_DIR}/usr/share/applications/frettool.desktop" "${APP_DIR}/"

# Generate icons from logo.png using any available tool
if command -v convert &> /dev/null; then
    echo "==> Generating icons with ImageMagick..."
    for size in 256 128 64 48 32; do
        convert logo.png -resize "${size}x${size}" \
            "${APP_DIR}/usr/share/icons/hicolor/${size}x${size}/apps/frettool.png" 2>/dev/null || true
    done
elif command -v rsvg-convert &> /dev/null && [ -f "logo.svg" ]; then
    echo "==> Generating icons with rsvg-convert..."
    for size in 256 128 64 48 32; do
        rsvg-convert -w "$size" -h "$size" logo.svg \
            -o "${APP_DIR}/usr/share/icons/hicolor/${size}x${size}/apps/frettool.png" 2>/dev/null || true
    done
else
    echo "Warning: No image conversion tool found. Place icons manually."
    if [ -f "icon.png" ]; then
        cp "icon.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/frettool.png"
    fi
fi

# Copy largest icon to AppDir root (AppImage requirement)
if [ -f "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/frettool.png" ]; then
    cp "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/frettool.png" "${APP_DIR}/frettool.png"
fi

# Create AppRun entry point
cat > "${APP_DIR}/AppRun" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="${APPDIR}/usr/bin:${PATH}"
export FRETTOOL_DATA_DIR="${APPDIR}/usr/share/FretTool"
exec "${APPDIR}/usr/bin/FretTool" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# Bundle locale files
if [ -d "locales" ]; then
    mkdir -p "${APP_DIR}/usr/share/FretTool/locales"
    cp -r locales/* "${APP_DIR}/usr/share/FretTool/locales/"
fi

# Locate appimagetool
APPIMAGETOOL=""
if command -v appimagetool &> /dev/null; then
    APPIMAGETOOL="appimagetool"
elif [ -f "./appimagetool-x86_64.AppImage" ]; then
    APPIMAGETOOL="./appimagetool-x86_64.AppImage"
else
    echo "Error: appimagetool not found."
    echo "Download from: https://github.com/AppImage/AppImageKit/releases"
    echo "Then run: appimagetool ${APP_DIR} ${OUTPUT}"
    echo "AppDir is ready at: ${APP_DIR}"
    exit 1
fi

# Build AppImage
echo "==> Building ${OUTPUT}..."
${APPIMAGETOOL} "${APP_DIR}" "${OUTPUT}"
chmod +x "${OUTPUT}"

echo "==> Done! AppImage created: ${OUTPUT}"
echo "Run it with: ./${OUTPUT}"
