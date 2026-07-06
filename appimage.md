# Creating an AppImage for FretTool

This guide explains how to package the FretTool PyInstaller binary into an
AppImage for distribution on Linux.

> **Quick start:** Run `./build_appimage.sh` on a Linux machine with the
> project files present. It automates all the steps below.

## Quick Build (Automated)

```bash
# 1. Ensure prerequisites (Python, appimagetool)
# 2. From the project root on Linux:
./build_appimage.sh
# 3. The output is FretTool-x86_64.AppImage
```

## Prerequisites

- Linux system (the AppImage must be built on Linux)
- `python3`, `pip`, `git`
- `appimagetool` (see below)
- The FretTool binary already compiled for Linux (via `build.sh` or `pyinstaller`)

### Install appimagetool

```bash
# Download appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Optional: move to PATH
sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
```

## Step-by-step

### 1. Build the PyInstaller binary for Linux

From the project root on a Linux machine:

```bash
chmod +x build.sh
./build.sh
```

This produces `dist/FretTool` (an ELF executable). If the build script fails
on the icon argument, ensure you have an `icon.ico` or `icon.png` in the
project root, or remove the `--icon` / `--add-data` flags and add the icon
manually to the AppDir later.

### 2. Create the AppDir structure

```bash
# Create the AppDir skeleton
mkdir -p FretTool.AppDir/usr/bin
mkdir -p FretTool.AppDir/usr/share/applications
mkdir -p FretTool.AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p FretTool.AppDir/usr/share/icons/hicolor/128x128/apps
mkdir -p FretTool.AppDir/usr/share/icons/hicolor/64x64/apps
mkdir -p FretTool.AppDir/usr/share/icons/hicolor/48x48/apps
mkdir -p FretTool.AppDir/usr/share/icons/hicolor/32x32/apps
```

### 3. Copy the binary

```bash
# Copy the PyInstaller binary
cp dist/FretTool FretTool.AppDir/usr/bin/
```

### 4. Create the .desktop file

Create `FretTool.AppDir/usr/share/applications/frettool.desktop`:

```desktop
[Desktop Entry]
Name=FretTool
Comment=Professional Guitar Fretboard Designer
Exec=usr/bin/FretTool
Icon=frettool
Terminal=false
Type=Application
Categories=Audio;Education;
StartupNotify=true
```

Also copy it to the top-level AppDir as required by AppImage:

```bash
cp FretTool.AppDir/usr/share/applications/frettool.desktop FretTool.AppDir/
```

### 5. Add icons

Generate a PNG icon from the existing logo or icon file:

```bash
# Convert the icon to required sizes (requires ImageMagick or similar)
convert logo.png -resize 256x256 FretTool.AppDir/usr/share/icons/hicolor/256x256/apps/frettool.png
convert logo.png -resize 128x128 FretTool.AppDir/usr/share/icons/hicolor/128x128/apps/frettool.png
convert logo.png -resize 64x64   FretTool.AppDir/usr/share/icons/hicolor/64x64/apps/frettool.png
convert logo.png -resize 48x48   FretTool.AppDir/usr/share/icons/hicolor/48x48/apps/frettool.png
convert logo.png -resize 32x32   FretTool.AppDir/usr/share/icons/hicolor/32x32/apps/frettool.png

# Fallback if you only have icon.ico (requires icotool from icoutils):
icotool -x icon.ico
```

Copy the largest icon to the AppDir root (required by AppImage):

```bash
cp FretTool.AppDir/usr/share/icons/hicolor/256x256/apps/frettool.png FretTool.AppDir/frettool.png
```

### 6. Create the AppRun entry point

Create `FretTool.AppDir/AppRun`:

```bash
#!/usr/bin/env bash
set -euo pipefail
APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="${APPDIR}/usr/bin:${PATH}"
exec "${APPDIR}/usr/bin/FretTool" "$@"
```

Make it executable:

```bash
chmod +x FretTool.AppDir/AppRun
```

### 7. Bundle the AppImage runtime

```bash
# Run appimagetool to produce the final AppImage
./appimagetool-x86_64.AppImage FretTool.AppDir FretTool-x86_64.AppImage

# Or if appimagetool is in PATH:
appimagetool FretTool.AppDir FretTool-x86_64.AppImage
```

### 8. Make executable and run

```bash
chmod +x FretTool-x86_64.AppImage
./FretTool-x86_64.AppImage
```

## Directory structure reference

```
FretTool.AppDir/
├── AppRun                          # Entry point (executable script)
├── frettool.desktop                # Desktop file (copy from usr/share)
├── frettool.png                    # Icon (256x256, copy from usr/share)
└── usr/
    ├── bin/
    │   └── FretTool                # PyInstaller-compiled binary
    └── share/
        ├── applications/
        │   └── frettool.desktop
        └── icons/
            └── hicolor/
                ├── 32x32/apps/frettool.png
                ├── 48x48/apps/frettool.png
                ├── 64x64/apps/frettool.png
                ├── 128x128/apps/frettool.png
                └── 256x256/apps/frettool.png
```

## Runtime data files

The app stores `projects.json` and `settings.json` in the platform-appropriate
data directory (NOT next to the executable):

| Platform | Data directory |
|----------|---------------|
| Linux    | `~/.local/share/FretTool/` |
| Windows  | `%APPDATA%/FretTool/` |
| macOS    | `~/Library/Application Support/FretTool/` |

On first launch the app automatically migrates any existing files from the old
executable-adjacent location to the new data directory.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FUSE: fuse-mount failed` | Run with `--appimage-extract-and-run` or install fuse: `sudo apt install fuse` |
| Missing icon in launcher | Verify `frettool.desktop` has the correct `Icon=frettool` entry and the PNG exists at the AppDir root |
| Binary not found | Check `AppRun` paths match the actual binary location inside `usr/bin/` |
| AppImage too large | Strip the binary: `strip dist/FretTool` before copying into the AppDir |
