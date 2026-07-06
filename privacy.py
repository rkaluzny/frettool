import customtkinter as ctk
import i18n
import sys

PRIVACY_TEXT = """Privacy Policy
==============

FretTool does not collect, store, or transmit any personal data.

• No analytics or telemetry
• No user tracking
• No internet connectivity except for opt-in update checks
• All project data is stored locally on your device

The update check feature sends a single anonymous request to
GitHub's public API to check for new versions. No personal
information is included in this request.

────────────────────────────────────────

Terms of Service
================

FretTool is provided "as is", without warranty of any kind.

You may use, modify, and distribute this software under the
terms of the MIT License.

The authors are not liable for any damages or losses arising
from the use of this software.

By using this software, you agree to these terms.
"""


def show_privacy_dialog(parent, on_accept=None):
    dialog = ctk.CTkToplevel(parent)
    dialog.title(i18n.tr("privacy.title"))
    dialog.resizable(True, True)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass
    dialog.minsize(500, 400)

    scroll = ctk.CTkScrollableFrame(dialog, corner_radius=16)
    scroll.pack(fill="both", expand=True, padx=20, pady=20)

    label = ctk.CTkLabel(
        scroll,
        text=PRIVACY_TEXT,
        font=("Arial", 13),
        justify="left",
        anchor="w",
        wraplength=560,
    )
    label.pack(fill="both", expand=True, padx=10, pady=10)

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=(0, 20))

    def on_accept_clicked():
        dialog.destroy()
        if on_accept:
            on_accept()

    ctk.CTkButton(btn_frame, text=i18n.tr("privacy.accept"), height=40, command=on_accept_clicked).pack(side="right")

    dialog.update_idletasks()
    dialog.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)
