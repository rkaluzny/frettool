<p align="center">
  <img src="logo.png" alt="FretTool" width="200">
</p>

# FretTool — v1.2.3

A Python application for designing guitar (and other string instrument) fretboard diagrams, chords, scales, and custom fingerings. Built with CustomTkinter.

## Features

### Core
- **Interactive Fretboard**: Click on string/fret intersections to place/remove notes
- **Multiple Instruments**: 2–12 strings, adjustable fret count (1–24)
- **Fret Markers**: Automatic position markers at standard frets (3, 5, 7, 9, 12, etc.)
- **Muted / X Markers**: Right-click on any position to mark as muted/open string

### Note Input & Editing
- **Standard Dots**: Left-click to place circular dots
- **Barres**: Form automatically when 2+ adjacent standard (circle) dots exist on the same fret
- **Barre Color Cycling**: Hover anywhere on a barre and scroll the mouse wheel (or two-finger touchpad) to cycle all barre dots through preset colours — a popup shows the colour palette
- **Barre Splitting**: Hover a dot within a barre and press ↑/↓ to split the barre at that string boundary
- **Special Notation**:
  - Ctrl+Click: square note
  - Shift+Click: triangle note
  - Alt+Click: smaller dot
  - Ctrl+Shift+Click: square (takes priority)
- **Note Labels**: Right-click an existing dot to set a 2-character label and/or per-dot colour
- **Fret Labels**: Double-click above the fret numbers to add text labels to frets
- **Colour Cycling**: Hover any dot and scroll the mouse wheel to cycle through preset colours with a live preview palette
- **Multi-Select**: Ctrl+RightClick to select multiple dots; Delete/Backspace removes all selected dots; colour cycling applies to all selected dots at once
- **Dot Properties Hotkey**: Press `P` while hovering a dot to open its properties dialog
- **Delete Key**: Press Delete or Backspace to remove the hovered dot or all selected dots

### Export
- **PDF Export**: High-quality multi-fretboard PDF via ReportLab
- **SVG Export**: Vector export of all fretboards (individual files)
- **PNG Export**: Raster image export of the current fretboard
- **Keyboard Shortcut**: Ctrl+P for quick PDF export
- **Symbol Mapping**: `b`/`#` converted to `♭`/`♯` in PDF output

### Undo / Redo
- **Undo/Redo Buttons**: ↶ and ↷ in the editor toolbar
- **Keyboard Shortcuts**: Ctrl+Z (undo), Ctrl+Y (redo)
- **History Depth**: Up to 20 states per fretboard

### Copy / Paste Fretboard
- **Copy**: Ctrl+C or the "Copy" button in the sidebar duplicates the current fretboard
- **Paste**: Ctrl+V or the "Paste" button creates a new fretboard from the clipboard
- The copy is preserved across fretboard switches

### Dashboard Search
- **Search Bar**: Filter projects by name in real-time from the dashboard
- **Project Preview**: Each card shows a mini fretboard preview of the first fretboard

### Configurable Hotkeys
- **Custom Bindings**: Every action can be re-bound to any key combination
- **Hotkey Recorder**: Press a key combination to record it in the settings dialog
- **Conflict Detection**: Settings warn about duplicate key assignments before saving
- **Persistent**: Hotkey overrides are saved to `settings.json`
- **Categories**: Actions organized into Editor, Dashboard, and General groups

### Internationalization (i18n)
- **10 Languages**: English, Deutsch, Polski, Русский, Español, Français, 中文, 日本語, עברית, العربية
- **Full UI Translation**: All labels, tooltips, dialogs, and help text
- **RTL Support**: Right-to-left layout for Hebrew and Arabic

### Settings (Tabbed Dialog)
- **General**: Appearance mode (Dark/Light), default string/fret count, language
- **Dimensions**: String spacing, fret spacing, margins, dot sizes
- **Colors**: Preset colour palette, default dot colour, fret line colours
- **Hotkeys**: Re-bind any action to a custom key combination
- **About**: Version info, license, privacy policy

### Project Management
- **Save/Load**: JSON-based project files stored in the platform data directory
- **Multiple Fretboards**: Many fretboards per project with tab navigation
- **Auto-Save**: Automatic saving on every change
- **Rename/Delete**: Manage projects and fretboards from the dashboard
- **JSON Backup**: Export all projects or a single project as JSON for backup or sharing; import projects from JSON files

### User Experience
- **Dark/Light Mode**: Adaptive UI follows system preference
- **Scrollable Sidebar**: Settings not cropped on small windows
- **Dynamic Fretboard**: Automatically resizes to fill available width
- **Built-in Help**: `?` button available from both dashboard and editor
- **Update Checker**: Periodic check for new versions via GitHub API
- **Privacy**: First-launch dialog explaining data handling (no telemetry)
- **Multi-Language**: 10 languages with RTL support for Hebrew and Arabic

## Getting Started (from source)

Run FretTool directly from source without a pre-built binary.

### Prerequisites
- Python 3.7+
- pip
- git

### Windows
```powershell
git clone https://github.com/rkaluzny/frettool.git
cd frettool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### macOS / Linux
```bash
git clone https://github.com/rkaluzny/frettool.git
cd frettool
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

### Linux (Debian/Ubuntu) — Tkinter dependency
```bash
sudo apt install python3-tk
# then follow the macOS/Linux steps above
```

### Fedora
```bash
sudo dnf install python3-tkinter
```

## Usage

1. **Create a project** from the dashboard via `+ New Project`
2. **Place dots** by left-clicking on string/fret intersections
3. **Barres form automatically** — place standard (circle) dots on adjacent strings at the same fret
4. **Add labels** by right-clicking an existing dot
5. **Remove notes** by left-clicking an existing dot (first click selects barres, second removes)
6. **Multi-Select**: Ctrl+RightClick on notes to select multiple; Delete removes all selected
7. **Copy/Paste**: Ctrl+C copies the current fretboard, Ctrl+V pastes a duplicate
8. **Export** with the PDF/SVG/PNG buttons or Ctrl+P for PDF
9. **Open help** via the `?` button in the dashboard or editor toolbar
10. **Customize hotkeys** in Settings → Hotkeys tab
11. **Backup/Restore**: Use "Export All" / "Import" buttons on the dashboard for JSON backup

## Hotkeys

Default keyboard shortcuts — all re-bindable in Settings:

| Action | Default |
|--------|---------|
| New Project | Ctrl+N |
| Open Settings | Ctrl+, |
| Show Help | Ctrl+H |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Export PDF | Ctrl+P |
| Save | Ctrl+S |
| Back to Dashboard | Ctrl+Shift+D |
| New Fretboard | Ctrl+Shift+N |
| Remove Fretboard | Ctrl+Shift+R |
| Rename Project | Ctrl+W |
| Focus Chord Name | Ctrl+Q |
| Focus Description | Ctrl+T |
| Dot Properties | P |
| Toggle Barres | Alt+B |
| Copy Fretboard | Ctrl+C |
| Paste Fretboard | Ctrl+V |
| Multi-select | Ctrl+RightClick |
| Delete selected | Delete / Backspace |
| Barre split up | ↑ |
| Barre split down | ↓ |

## Data Storage

Projects and settings are stored per-user in the platform data directory:

| Platform | Path |
|----------|------|
| Windows  | `%APPDATA%\FretTool\` |
| macOS    | `~/Library/Application Support/FretTool/` |
| Linux    | `~/.local/share/FretTool/` |

On first launch, existing files from the old executable-adjacent location are automatically migrated.

## Project Structure

```
FretTool/
├── main.py              # Entry point
├── app.py               # Main application class (window, bindings)
├── models.py            # Data models (FretboardData, ProjectData)
├── canvas.py            # Fretboard rendering and interaction
├── views.py             # Dashboard and editor UI
├── persistence.py       # Project save/load
├── settings.py          # User settings & hotkey defaults
├── hotkeys.py           # Hotkey management and recording
├── i18n.py              # Internationalization system
├── constants.py         # Config, version, colors, help text
├── export.py            # PDF export
├── barre_utils.py       # Barre grouping algorithm
├── updater.py           # Update checker (GitHub API)
├── privacy.py           # Privacy policy dialog
├── locales/             # Translation files (10 languages)
│   ├── en.json
│   ├── de.json
│   ├── pl.json
│   ├── ru.json
│   ├── es.json
│   ├── fr.json
│   ├── zh.json
│   ├── ja.json
│   ├── he.json
│   └── ar.json
├── docs/                # Additional documentation
├── requirements.txt     # Python dependencies
├── FretTool.spec        # PyInstaller spec (Linux/macOS)
├── main.spec            # Alternative PyInstaller spec
├── FretTool.iss         # Inno Setup installer script
├── build.bat            # Windows build script
├── build.sh             # Linux/macOS build script
├── build_macos.sh       # macOS-specific build script
├── build_appimage.sh    # AppImage build script
├── appimage.md          # AppImage packaging guide
├── icon.ico             # Windows icon
├── icon.icns            # macOS icon
├── logo.png             # Logo for README
└── README.md
```

## Building from Source

### Windows (PyInstaller)
```powershell
build.bat
```
Produces `dist/FretTool.exe`.

### Linux / macOS (PyInstaller)
```bash
chmod +x build.sh
./build.sh
```
Produces `dist/FretTool` (ELF / Mach-O binary).

### Linux AppImage
```bash
./build_appimage.sh
```
Produces `FretTool-x86_64.AppImage`.

### Windows Installer (Inno Setup)
Open `FretTool.iss` in Inno Setup Compiler and compile. Requires the PyInstaller binary built by `build.bat`.

## Dependencies

| Package | Purpose |
|---------|---------|
| customtkinter | Modern themed Tkinter GUI widgets |
| pillow | Image processing (icons, rendering) |
| reportlab | PDF generation |
| pyinstaller | Packaging into standalone executable |

## License

MIT
