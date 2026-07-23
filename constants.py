import tkinter as tk
from typing import Tuple, Optional

import customtkinter as ctk

import i18n
import sys

VERSION = "1.2.3"

HELP_TEXT = """\
FretTool — Fretboard Diagram Editor
====================================

Create and edit guitar (or other string instrument) fretboard diagrams.
Place notes, form barres, add labels, and export to PDF/SVG/PNG.

--- GETTING STARTED ---
• Click "+ New Project" on the dashboard to start.
• Click a project to open the editor.
• Use the fretboard tabs in the sidebar to switch between fretboards.

--- PLACING & REMOVING NOTES ---
• Left-click on any string/fret intersection -> places a circular dot.
• Left-click an existing dot -> removes it.
• Left-click a dot that is part of a barre: first click selects the
  barre (highlights it red), second click removes that note.
• Modifier keys while left-clicking:
  Ctrl+Click  -> square note
  Shift+Click -> triangle note
  Alt+Click   -> smaller dot
  Ctrl+Shift+Click -> square (takes priority over triangle)

--- SPECIAL NOTATION ---
• Double-click in the empty area above the fret numbers -> add a
  text label to a fret (e.g. "C", "Am").
• Right-click on an existing note -> open the dot properties dialog
  to set a 2-character label and/or override the dot colour.
• Ctrl+RightClick on a note -> toggles multi-selection.
  Select multiple notes to delete them all or cycle their colour together.

--- MUTED / X MARKERS ---
• Right-click on any string/fret intersection -> adds an X marker
  (muted/open string notation).
• Right-click on a string to the left of the nut (fret 0 area) -> also
  adds an X marker and removes any existing dot on that string.
• Left-click or right-click an X marker -> removes it.

--- BARRES ---
Barres are formed AUTOMATICALLY when you place 2 or more adjacent
standard (circle) dots on the same fret. Non-circle or small dots
break the barre grouping on that fret.

• Hover over any note in a barre and scroll the mouse wheel (or
  two-finger touchpad) to cycle all barre dots through the preset
  colours at once. A popup palette shows the available colours.
• To split a barre at a specific string, hover the dot just below
  the split point and press:
  ↑ (Arrow Up)   -> split above the hovered dot
  ↓ (Arrow Down) -> split below the hovered dot
  Press the same key again to merge the split.
• To disable barres entirely for a fretboard, check the
  "Disable barres" box in the sidebar settings.

--- SELECTING & DELETING ---
• Click a barre to select it (highlighted red). Click again to remove
  one note from the barre.
• Click a standalone dot to remove it.
• Press Delete or Backspace -> removes the currently hovered dot
  (or all selected dots if multi-selection is active).
• Use the fretboard settings in the sidebar to adjust string count,
  fret count, tuning, and delete the entire fretboard.

--- COPY / PASTE FRETBOARD ---
• Click the "Copy" button in the sidebar (or press Ctrl+C) to copy
  the current fretboard.
• Click the "Paste" button (or press Ctrl+V) to create a duplicate
  as a new fretboard in the same project.

--- FRETBOARD SETTINGS (SIDEBAR) ---
• Dot color: default colour for new dots.
• Disable barres checkbox.
• Copy / Paste buttons for duplicating fretboards.
• Strings: number of strings (2-12).
• Frets: number of frets (1-24).
• Delete Fretboard button.

--- UNDO / REDO ---
• ↶ and ↷ buttons in the editor toolbar undo/redo changes.
• The editor automatically saves to disk after every change.

--- EXPORTING ---
• Click the "PDF" button in the toolbar -> exports all fretboards
  as a high-quality PDF via ReportLab.
• Click "SVG" -> exports all fretboards as individual SVG files.
• Click "PNG" -> exports the current fretboard as a PNG image.
• Ctrl+P also triggers PDF export.

--- PROJECT MANAGEMENT ---
• The dashboard lists all saved projects. Click to open.
• Rename and delete projects from the dashboard cards.
• Use the search bar to filter projects by name.
• Export All / Import buttons on the dashboard for JSON backup.
• Projects are saved automatically to your data directory.

--- CUSTOMIZATION (SETTINGS) ---
• Open "Settings" from the dashboard to configure:
  Dark/Light mode, default fret/string count, barre behaviour,
  visual dimensions (spacing, margins, dot sizes), and the list
  of preset colours used for mouse wheel colour cycling.
• The Hotkeys tab warns about conflicting key assignments.
"""


def show_help(parent):
    import customtkinter as ctk
    import tkinter.font as tkfont

    win = ctk.CTkToplevel(parent)
    win.title(i18n.tr("help.title", version=VERSION))
    win.resizable(True, True)
    win.transient(parent)
    if sys.platform == "darwin":
        try:
            win.attributes('-type', 'dialog')
        except:
            pass
    win.minsize(600, 400)

    try:
        fixed_font = tkfont.nametofont("TkFixedFont").actual()["family"]
    except:
        fixed_font = "Courier"

    scroll = ctk.CTkScrollableFrame(win, corner_radius=16)
    scroll.pack(fill="both", expand=True, padx=18, pady=18)

    label = ctk.CTkLabel(
        scroll,
        text=i18n.tr("help.content"),
        font=(fixed_font, 12),
        justify="left",
        anchor="w",
    )
    label.pack(fill="both", expand=True)

    btn_close = ctk.CTkButton(scroll, text=i18n.tr("help.close"), command=win.destroy, width=100)
    btn_close.pack(pady=(15, 5))

    win.update_idletasks()
    win.focus_set()
    win.grab_set()

    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)


def get_colors():
    """Return colors based on system appearance mode"""
    try:
        mode = ctk.get_appearance_mode()
    except:
        mode = "Dark"
    if mode == "Light":
        return {
            "bg": "#f1f5f9",
            "surface": "#fef9ee",
            "surface_hover": "#fef3d1",
            "accent": "#ea580c",
            "text": "#1e293b",
            "text_muted": "#64748b",
            "fret_line": "#78716c",
            "string": "#1e293b",
            "dot": "#2563eb",
            "dot_hover": "#3b82f6",
            "dot_selected": "#dc2626",
            "dot_small": "#1e40af",
            "marker": "#94a3b8",
            "nut": "#44403c"
        }
    else:
        return {
            "bg": "#1a1a2e",
            "surface": "#252538",
            "surface_hover": "#2d2d44",
            "accent": "#ff9f43",
            "text": "#ffffff",
            "text_muted": "#888899",
            "fret_line": "#666677",
            "string": "#aaaaaa",
            "dot": "#4cc9f0",
            "dot_hover": "#7dd3fc",
            "dot_selected": "#ff6b6b",
            "dot_small": "#2a8cba",
            "marker": "#555566",
            "nut": "#e8dcc5"
        }

CONFIG = {
    "app_name": "FretTool",
    "default_frets": 12,
    "string_count": 6,
    "barres_enabled_default": True,
    "barre_min_strings": 2,
    "colors": get_colors(),
    "dimensions": {
        "string_spacing": 55,
        "fret_spacing": 65,
        "margin_top": 80,
        "margin_bottom": 80,
        "margin_side": 60,
        "nut_width": 12,
        "dot_radius": 14,
        "dot_small_radius": 8,
        "marker_radius": 8,
        "barre_half_width": 14,
        "barre_outline_width": 2,
        "barre_marker_radius": 3
    }
}

# Preset colors for scrolling - will be updated by settings
PRESET_COLORS = [
    "#ff6b6b",  # red
    "#ffd43b",  # yellow
    "#cc5de8",  # purple
    "#20c997",  # teal
]

# Apply settings on import
try:
    from settings import SettingsManager
    SettingsManager.apply_to_config()
except:
    pass

FRET_MARKERS = {3: 1, 5: 1, 7: 1, 9: 1, 12: 2, 15: 1, 17: 1, 19: 1, 21: 1, 24: 2}

# Symbol mappings for music notation
SYMBOL_MAP = {
    "b": "♭",
    "#": "♯"
}

# Reverse mapping for PDF export (avoid unicode issues)
REVERSE_SYMBOL_MAP = {"♭": "b", "♯": "#"}

def reverse_symbol_map(text: str) -> str:
    """Replace music symbols with original characters for PDF export"""
    if not text:
        return text
    return ''.join(REVERSE_SYMBOL_MAP.get(char, char) for char in text)

def hex_to_rgb01(hex_color: str) -> Tuple[float, float, float]:
    if not hex_color:
        return (0.0, 0.0, 0.0)
    color = hex_color.strip().lstrip("#")
    if len(color) != 6:
        return (0.0, 0.0, 0.0)
    r = int(color[0:2], 16) / 255.0
    g = int(color[2:4], 16) / 255.0
    b = int(color[4:6], 16) / 255.0
    return (r, g, b)

def apply_symbol_map(text: str) -> str:
    """Replace b and # with music symbols"""
    if not text:
        return text
    result = ""
    for char in text:
        result += SYMBOL_MAP.get(char, char)
    return result

def ask_text(parent, title: str, prompt: str, initial: str = "") -> Optional[str]:
    import customtkinter as ctk
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.resizable(False, False)
    win.transient(parent)
    if sys.platform == "darwin":
        try:
            win.attributes('-type', 'dialog')
        except:
            pass

    result: dict = {"value": None}
    entry_var = tk.StringVar(value=initial or "")

    frame = ctk.CTkFrame(win, corner_radius=16)
    frame.pack(padx=18, pady=18, fill="both", expand=True)

    lbl = ctk.CTkLabel(frame, text=prompt, font=("Arial", 13), text_color=CONFIG["colors"]["text"])
    lbl.pack(anchor="w", pady=(8, 10), padx=12)

    entry = ctk.CTkEntry(frame, textvariable=entry_var, width=240)
    entry.pack(fill="x", padx=12, pady=(0, 12))
    entry.focus_set()
    entry.select_range(0, "end")

    btns = ctk.CTkFrame(frame, fg_color="transparent")
    btns.pack(fill="x", padx=12, pady=(0, 6))

    def on_ok():
        result["value"] = entry.get()
        win.destroy()

    def on_cancel():
        result["value"] = None
        win.destroy()

    def on_closing():
        result["value"] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_closing)

    btn_cancel = ctk.CTkButton(btns, text=i18n.tr("dialogs.cancel"), fg_color="transparent", border_width=1, text_color=CONFIG["colors"]["text"], command=on_cancel, width=90)
    btn_cancel.pack(side="right")
    btn_ok = ctk.CTkButton(btns, text=i18n.tr("dialogs.ok"), command=on_ok, width=90)
    btn_ok.pack(side="right", padx=(0, 10))

    win.bind("<Return>", lambda e: on_ok())
    win.bind("<Escape>", lambda e: on_cancel())

    win.update_idletasks()
    win.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result["value"]


def ask_dot_properties(parent, default_color: str, initial_label: str = "", initial_color: str = "") -> Optional[Tuple[str, str]]:
    import customtkinter as ctk
    from tkinter import colorchooser
    win = ctk.CTkToplevel(parent)
    win.title(i18n.tr("editor.dot_properties.title"))
    win.resizable(False, False)
    win.transient(parent)
    if sys.platform == "darwin":
        try:
            win.attributes('-type', 'dialog')
        except:
            pass

    result: dict = {"value": None}
    label_var = tk.StringVar(value=(initial_label or "")[:2])
    color_var = tk.StringVar(value=initial_color or "")

    frame = ctk.CTkFrame(win, corner_radius=16)
    frame.pack(padx=18, pady=18, fill="both", expand=True)

    lbl = ctk.CTkLabel(frame, text=i18n.tr("editor.dot_properties.label"), font=("Arial", 13),
                       wraplength=300, justify="left")
    lbl.pack(anchor="w", pady=(8, 10), padx=12)

    entry = ctk.CTkEntry(frame, textvariable=label_var, width=280)
    entry.pack(anchor="w", padx=12, pady=(0, 10))
    entry.focus_set()
    entry.select_range(0, "end")

    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(0, 10))

    def preview_color() -> str:
        return color_var.get() or default_color

    btn_pick = ctk.CTkButton(row, text=i18n.tr("editor.dot_properties.pick_color"), width=110, command=lambda: _pick_color())
    btn_pick.pack(side="left")

    btn_preview = ctk.CTkButton(row, text=" ", width=40, fg_color=preview_color(), hover_color=preview_color(), command=lambda: _pick_color())
    btn_preview.pack(side="left", padx=10)

    def _pick_color():
        chosen = colorchooser.askcolor(color=preview_color(), title=i18n.tr("editor.dot_color_dialog.title"))
        if chosen and chosen[1]:
            color_var.set(chosen[1])
            c = preview_color()
            btn_preview.configure(fg_color=c, hover_color=c)

    def on_reset():
        color_var.set("")
        c = preview_color()
        btn_preview.configure(fg_color=c, hover_color=c)

    btn_reset = ctk.CTkButton(row, text=i18n.tr("editor.dot_properties.use_default"), width=110, fg_color="transparent", border_width=1, text_color=CONFIG["colors"]["text"], command=on_reset)
    btn_reset.pack(side="left")

    btns = ctk.CTkFrame(frame, fg_color="transparent")
    btns.pack(fill="x", padx=12, pady=(6, 6))

    def on_ok():
        result["value"] = ((label_var.get() or "")[:2], color_var.get() or "")
        win.destroy()

    def on_cancel():
        result["value"] = None
        win.destroy()

    def on_closing():
        result["value"] = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_closing)

    btn_cancel = ctk.CTkButton(btns, text=i18n.tr("dialogs.cancel"), fg_color="transparent", border_width=1, text_color=CONFIG["colors"]["text"], command=on_cancel, width=90)
    btn_cancel.pack(side="right")
    btn_ok = ctk.CTkButton(btns, text=i18n.tr("dialogs.ok"), command=on_ok, width=90)
    btn_ok.pack(side="right", padx=(0, 10))

    win.bind("<Return>", lambda e: on_ok())
    win.bind("<Escape>", lambda e: on_cancel())

    win.update_idletasks()
    win.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result["value"]