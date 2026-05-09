<p align="center">
  <img src="logo.png" alt="FretTool" width="200">
</p>

# FretTool - Professional Guitar Fretboard Designer

FretTool is a comprehensive Python application for designing and visualizing guitar fretboards, chords, scales, and custom fingerings. Built with CustomTkinter and featuring modern UI design, it's perfect for guitar teachers, students, and musicians who need to create professional-quality fretboard diagrams.

## Features

### Core Functionality
- **Interactive Fretboard Design**: Click to place notes, click again to remove, and use modifier keys for special notation
- **Multiple Instrument Support**: Configure for different string counts (guitar, bass, ukulele, etc.)
- **Adjustable Fret Range**: Set the number of frets displayed (default 12, expandable as needed)
- **Position Markings**: Automatic fret markers at standard positions (3, 5, 7, 9, 12, etc.)

### Note Input & Editing
- **Standard Dots**: Left-click to place notes on strings and frets
- **Muted Strings**: Right-click on string left of nut to mark as muted (X)
- **Special Notation**: 
  - **Ctrl+Click**: Square notes
  - **Shift+Click**: Triangle notes
  - **Alt+Click**: Smaller dots
  - **Combinations**: Ctrl+Shift prioritizes square notation
- **Note Labels**: Add text labels to notes (double-click on fret for fret labels, right-click on note for note labels)
- **Color Customization**: 
  - Global dot color setting
  - Per-note color customization (right-click on note)
  - Mouse wheel color cycling on hovered notes
  - Preset color palette for quick selection

### Project Management
- **Save/Load Projects**: Store multiple fretboards in a single project
- **Project Metadata**: Name, creation date, and description for each project
- **Fretboard Organization**: Multiple fretboards per project for comparing variations
- **Persistent Storage**: Automatic saving of projects between sessions

### Export & Sharing
- **PDF Export**: Export individual fretboards or entire projects as high-quality PDFs
- **Print Ready**: Optimized layouts for printing and sharing
- **Data Portability**: JSON-based project files for easy sharing and version control

### User Experience
- **Modern Interface**: Clean, dark/light mode adaptive UI built with CustomTkinter
- **Responsive Design**: Works on various screen sizes and resolutions
- **Keyboard Shortcuts**: 
  - Ctrl+P: Export current fretboard as PDF
  - Modifier keys for special note types
- **Visual Feedback**: 
  - Hover previews for note placement
  - Selection highlights for editing
  - Grid snap for precise positioning
- **Contextual Help**: Intuitive right-click menus and dialogs

### Technical Features
- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Extensible Design**: Modular architecture for easy feature addition
- **Performance Optimized**: Efficient rendering for smooth interaction
- **Configuration System**: Adjustable dimensions, colors, and defaults
- **Symbol Mapping**: Automatic conversion of b/# to ♭/♯ for proper music notation

## Getting Started

### Installation
1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
   ```
   pip install customtkinter pillow
   ```
3. Run the application:
   ```
   python main.py
   ```

### Basic Usage
1. **Creating Notes**: Click on any string/fret intersection to place a dot
2. **Creating Barres**: Click multiple strings on the same fret - they'll automatically join into a barre
3. **Special Notes**: Use modifier keys while clicking:
   - Ctrl: Square note
   - Shift: Triangle note  
   - Alt: Smaller dot
   - Ctrl+Shift: Square (takes priority)
4. **Muting Strings**: Right-click on the string area left of the nut
5. **Adding Labels**: 
   - Double-click a fret number to add fret labels
   - Right-click on a note to add note labels and change colors
6. **Navigating Projects**: 
   - Use the dashboard to create/open projects
   - Switch between fretboards within a project
   - Save your work automatically

## Advanced Features

### Barre Detection Algorithm
The application intelligently detects when you're creating barre chords:
- When multiple strings are selected on the same fret
- AND none of those strings have special types (triangle/square)
- THEN displays them as a connected barre rather than individual dots
- Special note types (triangle/square) always display individually to preserve their distinct visual meaning

### Color System
- **Global Settings**: Set default dot color in settings
- **Per-Note Overrides**: Right-click any note to set custom color
- **Preset Palette**: Scroll through predefined colors with mouse wheel on hovered notes
- **Appearance Adaptive**: Colors automatically adjust for light/dark mode

### Export Quality
- Vector-based PDF output for crisp, scalable graphics
- Proper text rendering for labels and symbols
- Optimized layout for standard paper sizes
- Transparent backgrounds available upon request

## Development

FretTool is built with:
- **Python 3.7+**: Core language
- **CustomTkinter**: Modern Tkinter wrapper for beautiful UI
- **Pillow**: Image handling for icons and exports
- **JSON**: Project file format for easy parsing and sharing

### Project Structure
```
FretTool/
├── main.py              # Application entry point
├── app.py               # Main application class
├── models.py            # Data models (ProjectData, FretboardData)
├── canvas.py            # Fretboard rendering and interaction
├── views.py             # UI components (Dashboard, Editor)
├── persistence.py       # Project save/load functionality
├── settings.py          # User settings management
├── constants.py         # Configuration, colors, and utilities
├── www/                 # Web assets (if applicable)
├── icon.ico             # Application icon
└── README.md            # This file
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests, open issues, or suggest features.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with CustomTkinter for the modern UI components
- Inspired by the need for better guitar teaching tools
- Thanks to all musicians and educators who provide feedback