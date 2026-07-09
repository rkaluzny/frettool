import sys
import i18n
from settings import SettingsManager, DEFAULT_HOTKEYS


def get_all_hotkeys():
    settings = SettingsManager.load_settings()
    stored = settings.get("hotkeys", {})
    hotkeys = {}
    hotkeys.update(DEFAULT_HOTKEYS)
    hotkeys.update(stored)
    return hotkeys


def save_all_hotkeys(hotkeys):
    settings = SettingsManager.load_settings()
    settings["hotkeys"] = hotkeys
    SettingsManager.save_settings(settings)


def event_to_sequence(event):
    keysym = event.keysym
    if keysym in ("Control_L", "Control_R", "Alt_L", "Alt_R", "Shift_L", "Shift_R",
                  "Meta_L", "Meta_R", "Super_L", "Super_R"):
        return None

    mods = []
    if sys.platform == "win32":
        if event.state & 0x0004:
            mods.append("Control")
        if event.state & 0x20000:
            mods.append("Alt")
        if event.state & 0x0001:
            mods.append("Shift")
    elif sys.platform == "darwin":
        if event.state & 0x0010:
            mods.append("Control")
        if event.state & 0x0008:
            mods.append("Alt")
        if event.state & 0x0001:
            mods.append("Shift")
    else:
        if event.state & 0x0004:
            mods.append("Control")
        if event.state & 0x0008:
            mods.append("Alt")
        if event.state & 0x0001:
            mods.append("Shift")

    if mods:
        if len(keysym) == 1:
            keysym = keysym.lower()
        return f"<{'-'.join(mods)}-{keysym}>"
    else:
        return keysym.lower()


def record_hotkey_dialog(parent, current_sequence):
    import customtkinter as ctk

    win = ctk.CTkToplevel(parent)
    win.title(i18n.tr("hotkeys.record_dialog.title"))
    win.resizable(False, False)
    win.transient(parent)
    if sys.platform == "darwin":
        try:
            win.attributes('-type', 'dialog')
        except:
            pass

    result = {"value": current_sequence}

    frame = ctk.CTkFrame(win, corner_radius=16)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    from constants import CONFIG

    ctk.CTkLabel(frame, text=i18n.tr("hotkeys.record_dialog.prompt"), font=("Arial", 13),
                 text_color=CONFIG["colors"]["text"]).pack(pady=(10, 15))

    display_var = ctk.StringVar(value="...")
    display = ctk.CTkEntry(frame, textvariable=display_var, width=250,
                           justify="center", font=("Arial", 14),
                           text_color=CONFIG["colors"]["text"])
    display.pack(pady=(0, 15))
    display.focus_set()

    def on_key(event):
        seq = event_to_sequence(event)
        if seq:
            display_var.set(seq)
            result["value"] = seq

    def on_ok():
        win.destroy()

    def on_cancel():
        result["value"] = current_sequence
        win.destroy()

    win.bind("<KeyPress>", on_key)

    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x", pady=(5, 10))

    from i18n import tr
    ctk.CTkButton(btn_frame, text=tr("dialogs.cancel"), fg_color="transparent", border_width=1,
                  text_color=CONFIG["colors"]["text"], command=on_cancel, width=80).pack(side="left", padx=(0, 10))
    ctk.CTkButton(btn_frame, text=tr("dialogs.ok"), command=on_ok, width=80).pack(side="left")

    win.update_idletasks()
    win.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (300 // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (200 // 2)
    win.geometry(f"+{x}+{y}")

    parent.wait_window(win)
    return result["value"]
