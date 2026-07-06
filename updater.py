import os
import sys
import json
import threading
import tempfile
import subprocess
import ssl
from urllib.request import urlopen, Request
from urllib.error import URLError
from constants import VERSION
import i18n

GITHUB_REPO = "rkaluzny/frettool"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"


def _parse_version(version_str):
    v = version_str.lstrip("v")
    parts = v.split(".")
    return tuple(int(p) for p in parts)


def _get_platform_asset_suffix():
    if sys.platform == "win32":
        return ".exe"
    elif sys.platform == "linux":
        return ".AppImage"
    elif sys.platform == "darwin":
        return ".dmg"
    return None


def _is_newer_version(latest_version):
    try:
        return _parse_version(latest_version) > _parse_version(VERSION)
    except:
        return False


def _fetch_latest_release():
    req = Request(GITHUB_API, headers={"User-Agent": "FretTool-Updater/1.0"})
    context = ssl._create_unverified_context()
    with urlopen(req, timeout=10, context=context) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_for_updates():
    """Returns (info_dict, None) if update available,
       (None, None) if already up to date,
       (None, error_msg) if the check failed."""
    try:
        data = _fetch_latest_release()
        tag = data.get("tag_name", "")
        if not tag:
            return (None, "No release tag found")
        latest = tag.lstrip("v")
        if not _is_newer_version(latest):
            return (None, None)

        download_url = None
        suffix = _get_platform_asset_suffix()
        if suffix:
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(suffix):
                    download_url = asset["browser_download_url"]
                    break

        info = {
            "latest_version": latest,
            "current_version": VERSION,
            "download_url": download_url,
            "release_url": data.get("html_url", GITHUB_URL + "/releases/latest"),
            "release_name": data.get("name", tag),
            "release_body": data.get("body", ""),
            "tag_name": tag,
        }
        return (info, None)
    except Exception as e:
        print(f"Update check failed: {e}")
        return (None, str(e))


def download_update(url, destination, progress_callback=None):
    context = ssl._create_unverified_context()
    req = Request(url, headers={"User-Agent": "FretTool-Updater/1.0"})
    with urlopen(req, context=context) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 8192
        with open(destination, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total > 0:
                    progress_callback(downloaded / total)


def install_update(filepath):
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        os.chmod(filepath, 0o755)
        subprocess.Popen([filepath])


def show_update_dialog(parent, update_info):
    import customtkinter as ctk

    dialog = ctk.CTkToplevel(parent)
    dialog.title(i18n.tr("updates.available"))
    dialog.resizable(True, True)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass
    dialog.minsize(480, 350)

    frame = ctk.CTkFrame(dialog, corner_radius=16)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        frame,
        text=i18n.tr("updates.available_desc", latest=update_info["latest_version"], current=update_info["current_version"]),
        font=("Arial", 16, "bold"),
        wraplength=440,
        justify="left",
    ).pack(anchor="w", pady=(0, 12))

    if update_info.get("release_body"):
        scroll = ctk.CTkScrollableFrame(frame, height=150, corner_radius=8)
        scroll.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(
            scroll,
            text=update_info["release_body"][:2000],
            font=("Arial", 12),
            justify="left",
            anchor="w",
            wraplength=420,
        ).pack(fill="x", padx=8, pady=8)

    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x")

    result = {"action": None}

    def on_download():
        result["action"] = "download"
        dialog.destroy()

    def on_later():
        result["action"] = "later"
        dialog.destroy()

    ctk.CTkButton(btn_frame, text=i18n.tr("updates.download"), height=38, command=on_download).pack(side="right", padx=(8, 0))
    ctk.CTkButton(btn_frame, text=i18n.tr("updates.later"), height=38, fg_color="transparent", border_width=1, command=on_later).pack(side="right")

    dialog.update_idletasks()
    dialog.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)
    return result["action"]


def show_update_progress(parent, update_info):
    import customtkinter as ctk

    dialog = ctk.CTkToplevel(parent)
    dialog.title(i18n.tr("updates.downloading"))
    dialog.resizable(False, False)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass
    dialog.geometry("400x150")

    frame = ctk.CTkFrame(dialog, corner_radius=16)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(frame, text=i18n.tr("updates.downloading_desc", name=update_info.get("release_name", "")),
                 font=("Arial", 13), wraplength=360, justify="left").pack(anchor="w", pady=(0, 12))

    progress = ctk.CTkProgressBar(frame, width=350)
    progress.pack(pady=(0, 12))
    progress.set(0)

    status = ctk.CTkLabel(frame, text="0%", font=("Arial", 11))
    status.pack()

    def set_progress(pct):
        progress.set(pct)
        status.configure(text=f"{int(pct * 100)}%")
        dialog.update_idletasks()

    def on_complete():
        dialog.destroy()

    def on_error(msg):
        status.configure(text=i18n.tr("updates.download_error", error=msg))
        status.configure(text_color="red")

    return dialog, set_progress, on_complete, on_error


def show_up_to_date_dialog(parent):
    import customtkinter as ctk

    dialog = ctk.CTkToplevel(parent)
    dialog.title(i18n.tr("updates.no_update"))
    dialog.resizable(False, False)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass

    frame = ctk.CTkFrame(dialog, corner_radius=16)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        frame,
        text=i18n.tr("updates.no_update_desc", version=VERSION),
        font=("Arial", 14),
        wraplength=320,
        justify="left",
    ).pack(anchor="w", pady=(0, 15))

    ctk.CTkButton(frame, text=i18n.tr("dialogs.ok"), width=80, command=dialog.destroy).pack()

    dialog.update_idletasks()
    dialog.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)


def show_update_error_dialog(parent, error_msg=""):
    import customtkinter as ctk

    dialog = ctk.CTkToplevel(parent)
    dialog.title(i18n.tr("updates.error"))
    dialog.resizable(False, False)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass

    frame = ctk.CTkFrame(dialog, corner_radius=16)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(
        frame,
        text=i18n.tr("updates.error_desc"),
        font=("Arial", 14),
        wraplength=320,
        justify="left",
    ).pack(anchor="w", pady=(0, 15))

    if error_msg:
        ctk.CTkLabel(frame, text=error_msg, font=("Arial", 11),
                     text_color="gray", wraplength=320).pack(anchor="w", pady=(0, 15))

    ctk.CTkButton(frame, text=i18n.tr("dialogs.ok"), width=80, command=dialog.destroy).pack()

    dialog.update_idletasks()
    dialog.grab_set()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    parent.wait_window(dialog)
