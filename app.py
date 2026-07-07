import os
import sys
import threading
import customtkinter as ctk
import i18n
from views import DashboardView, EditorView
from models import ProjectData


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        try:
            if sys.platform == "linux":
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(resource_path("icon.ico"))
                    self.icon = ImageTk.PhotoImage(img)
                    self.wm_iconphoto(True, self.icon)
                except:
                    pass
            else:
                self.iconbitmap(resource_path("icon.ico"))
        except:
            pass
        from constants import CONFIG, VERSION
        self.title(i18n.tr("app.title", version=VERSION))
        self.geometry("1400x900")
        self.minsize(1200, 700)
        self.current_project: ProjectData = None
        self.editor = None

        # Bind Ctrl+P for printing globally
        self.bind("<Control-p>", self.on_print_shortcut)

        self.show_dashboard()
        self.after(100, self._first_run_checks)

    def on_print_shortcut(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.export("pdf")

    def _first_run_checks(self):
        self._check_privacy()
        self.after(3000, self._check_updates_background)

    def _check_privacy(self):
        from settings import SettingsManager
        settings = SettingsManager.load_settings()
        if not settings.get("privacy_accepted", False):
            from privacy import show_privacy_dialog
            def on_accept():
                s = SettingsManager.load_settings()
                s["privacy_accepted"] = True
                SettingsManager.save_settings(s)
            show_privacy_dialog(self, on_accept=on_accept)

    def _check_updates_background(self):
        from settings import SettingsManager
        settings = SettingsManager.load_settings()
        if settings.get("skip_update_check", False):
            return
        def check():
            from updater import check_for_updates
            info, error = check_for_updates()
            if info:
                self.after(0, lambda: self._handle_update_found(info))
        t = threading.Thread(target=check, daemon=True)
        t.start()

    def _handle_update_found(self, update_info):
        from updater import show_update_dialog, show_update_progress, download_update, install_update, show_update_error_dialog
        action = show_update_dialog(self, update_info)
        if action != "download":
            return
        dialog, set_progress, on_complete, on_error = show_update_progress(self, update_info)
        def download():
            try:
                import tempfile as tf
                suffix = ".exe" if sys.platform == "win32" else (".dmg" if sys.platform == "darwin" else ".AppImage")
                fd, path = tf.mkstemp(suffix=suffix, prefix="FretTool_")
                os.close(fd)
                def progress_cb(pct):
                    self.after(0, lambda: set_progress(pct))
                download_update(update_info["download_url"], path, progress_cb)
                self.after(0, on_complete)
                self.after(500, lambda: install_update(path, quit_callback=self.destroy))
            except Exception as e:
                self.after(0, lambda: show_update_error_dialog(self, str(e)))
        t = threading.Thread(target=download, daemon=True)
        t.start()

    def show_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.editor = None

        self.dashboard = DashboardView(self, on_open_project_callback=self.open_project)
        self.dashboard.pack(fill="both", expand=True)

    def open_project(self, project: ProjectData):
        self.current_project = project
        for widget in self.winfo_children():
            widget.destroy()

        self.editor = EditorView(self, project, on_back_callback=self.show_dashboard)
        self.editor.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.current_project:
            from persistence import ProjectStore
            ProjectStore.upsert_project(self.current_project)

        self.destroy()
