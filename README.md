<p align="center">
  <img src="logo.png" alt="FretTool" width="200">
</p>

# FretTool — v1.0.0

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
- **Barre Color Cycling**: Hover anywhere on a barre and scroll the mouse wheel (or two-finger touchpad) to change colour for all barre dots at once
- **Barre Splitting**: Hover a dot within a barre and press ↑/↓ to split the barre at that string boundary
- **Special Notation**:
  - Ctrl+Click: square note
  - Shift+Click: triangle note
  - Alt+Click: smaller dot
- **Note Labels**: Right-click an existing dot to set a 2-character label and/or per-dot colour
- **Fret Labels**: Double-click above the fret numbers to add text labels to frets
- **Colour Cycling**: Hover any dot and scroll the mouse wheel to cycle through preset colours

### Project Management
- **Save/Load**: JSON-based project files stored in the platform data directory
- **Multiple Fretboards**: Many fretboards per project
- **Auto-Save**: Automatic saving on every change
- **Rename/Delete**: Manage projects and fretboards from the dashboard

### Export
- **PDF Export**: Vector-quality fretboard diagrams via ReportLab
- **Ctrl+P**: Keyboard shortcut for PDF export
- **Symbol Mapping**: `b`/`#` converted to `♭`/`♯` in PDF output

### User Experience
- **Dark/Light Mode**: Adaptive UI follows system preference
- **Scrollable Sidebar**: Settings not cropped on small windows
- **Dynamic Fretboard**: Automatically resizes to fill available width
- **Built-in Help**: `?` button available from both dashboard and editor

## Getting Started (from source)

Run FretTool directly from source without a pre-built binary.

### Prerequisites
- Python 3.7+
- pip

### Windows
```powershell
git clone https://github.com/yourusername/FretTool.git
cd FretTool
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### macOS / Linux
```bash
git clone https://github.com/yourusername/FretTool.git
cd FretTool
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
6. **Export** with the `PDF` button or Ctrl+P
7. **Open help** via the `?` button in the dashboard or editor toolbar

## Data Storage

Projects and settings are stored per-user in the platform data directory:

| Platform | Path |
|----------|------|
| Windows  | `%APPDATA%\FretTool\` |
| macOS    | `~/Library/Application Support/FretTool/` |
| Linux    | `~/.local/share/FretTool/` |

## Project Structure

```
FretTool/
├── main.py              # Entry point
├── app.py               # Main application class
├── models.py            # Data models
├── canvas.py            # Fretboard rendering and interaction
├── views.py             # Dashboard and editor UI
├── persistence.py       # Project save/load
├── settings.py          # User settings
├── constants.py         # Config, version, colors, dialogs
├── export.py            # PDF export
├── barre_utils.py       # Barre grouping algorithm
├── FretTool.spec        # PyInstaller spec
├── icon.ico             # Application icon
├── requirements.txt     # Python dependencies
└── README.md
```

## License

MIT
