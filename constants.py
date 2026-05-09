import tkinter as tk
from typing import Tuple, Optional

import customtkinter as ctk
from typing import Tuple, Optional

# --- KONFIGURATION & KONSTANTEN ---
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
        "marker_radius": 8
    }
}

# Preset colors for scrolling - will be updated by settings
PRESET_COLORS = [
    "#4cc9f0",  # default blue
    "#ff6b6b",  # red
    "#51cf66",  # green
    "#ffd43b",  # yellow
    "#cc5de8",  # purple
    "#ff922b",  # orange
    "#20c997",  # teal
    "#f06595",  # pink
    "#5c7cfa",  # indigo
    "#e599f7",  # light purple
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
    win.grab_set()

    result: dict = {"value": None}
    entry_var = tk.StringVar(value=initial or "")

    frame = ctk.CTkFrame(win, corner_radius=16)
    frame.pack(padx=18, pady=18, fill="both", expand=True)

    lbl = ctk.CTkLabel(frame, text=prompt, font=("Arial", 13))
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

    btn_cancel = ctk.CTkButton(btns, text="Cancel", fg_color="transparent", border_width=1, text_color=("white", "black"), command=on_cancel, width=90)
    btn_cancel.pack(side="right")
    btn_ok = ctk.CTkButton(btns, text="OK", command=on_ok, width=90)
    btn_ok.pack(side="right", padx=(0, 10))

    win.bind("<Return>", lambda e: on_ok())
    win.bind("<Escape>", lambda e: on_cancel())

    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result["value"]

def ask_dot_properties(parent, default_color: str, initial_label: str = "", initial_color: str = "") -> Optional[Tuple[str, str]]:
    import customtkinter as ctk
    from tkinter import colorchooser
    win = ctk.CTkToplevel(parent)
    win.title("Dot properties")
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    result: dict = {"value": None}
    label_var = tk.StringVar(value=(initial_label or "")[:2])  # Allow up to 2 chars
    color_var = tk.StringVar(value=initial_color or "")

    frame = ctk.CTkFrame(win, corner_radius=16)
    frame.pack(padx=18, pady=18, fill="both", expand=True)

    lbl = ctk.CTkLabel(frame, text="Label (max 2 chars) and optional per-dot color:", font=("Arial", 13))
    lbl.pack(anchor="w", pady=(8, 10), padx=12)

    entry = ctk.CTkEntry(frame, textvariable=label_var, width=200)
    entry.pack(anchor="w", padx=12, pady=(0, 10))
    entry.focus_set()
    entry.select_range(0, "end")

    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(0, 10))

    def preview_color() -> str:
        return color_var.get() or default_color

    btn_pick = ctk.CTkButton(row, text="Pick color", width=110, command=lambda: _pick_color())
    btn_pick.pack(side="left")

    btn_preview = ctk.CTkButton(row, text=" ", width=40, fg_color=preview_color(), hover_color=preview_color(), command=lambda: _pick_color())
    btn_preview.pack(side="left", padx=10)

    def _pick_color():
        chosen = colorchooser.askcolor(color=preview_color(), title="Choose dot color")
        if chosen and chosen[1]:
            color_var.set(chosen[1])
            c = preview_color()
            btn_preview.configure(fg_color=c, hover_color=c)

    def on_reset():
        color_var.set("")
        c = preview_color()
        btn_preview.configure(fg_color=c, hover_color=c)

    btn_reset = ctk.CTkButton(row, text="Use default", width=110, fg_color="transparent", border_width=1, text_color=("white", "black"), command=on_reset)
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

    btn_cancel = ctk.CTkButton(btns, text="Cancel", fg_color="transparent", border_width=1, text_color=("white", "black"), command=on_cancel, width=90)
    btn_cancel.pack(side="right")
    btn_ok = ctk.CTkButton(btns, text="OK", command=on_ok, width=90)
    btn_ok.pack(side="right", padx=(0, 10))

    win.bind("<Return>", lambda e: on_ok())
    win.bind("<Escape>", lambda e: on_cancel())

    win.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (win.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result["value"]
