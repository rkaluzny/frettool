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
        self.dashboard = None

        self._bind_hotkeys()

        self.show_dashboard()
        self.after(100, self._first_run_checks)

    def _bind_hotkeys(self):
        from hotkeys import get_all_hotkeys
        hk = get_all_hotkeys()

        self.bind(hk["new_project"], self._on_new_project)
        self.bind(hk["open_settings"], self._on_open_settings)
        self.bind(hk["show_help"], self._on_show_help)
        self.bind(hk["export_pdf"], self.on_print_shortcut)
        self.bind(hk["rename_project"], self._on_rename_project)
        self.bind(hk["undo"], self._on_undo)
        self.bind(hk["redo"], self._on_redo)
        self.bind(hk["back_to_dashboard"], self._on_back_to_dashboard)
        self.bind(hk["new_fretboard"], self._on_new_fretboard)
        self.bind(hk["remove_fretboard"], self._on_remove_fretboard)
        self.bind(hk["save"], self._on_save)
        self.bind(hk["focus_chord_name"], self._on_focus_chord_name)
        self.bind(hk["focus_description"], self._on_focus_description)
        self.bind(hk["dot_properties"], self._on_dot_properties)
        self.bind(hk["toggle_barre"], self._on_toggle_barre)

    def rebind_hotkeys(self):
        self._bind_hotkeys()

    def on_print_shortcut(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.export("pdf")

    def _on_new_project(self, event=None):
        if self.dashboard and self.dashboard.winfo_exists():
            self.dashboard.create_new_project()

    def _on_open_settings(self, event=None):
        if self.editor and self.editor.winfo_exists():
            from views import open_settings_dialog
            open_settings_dialog(self.editor, on_save_callback=self.rebind_hotkeys)
        elif self.dashboard and self.dashboard.winfo_exists():
            self.dashboard.open_settings()

    def _on_show_help(self, event=None):
        from constants import show_help
        if self.editor and self.editor.winfo_exists():
            show_help(self.editor)
        elif self.dashboard and self.dashboard.winfo_exists():
            show_help(self.dashboard)

    def _on_rename_project(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.rename_project()

    def _on_undo(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.undo()

    def _on_redo(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.redo()

    def _on_back_to_dashboard(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.back_to_dashboard()

    def _on_new_fretboard(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.add_new_fretboard()

    def _on_remove_fretboard(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.delete_current_fretboard()

    def _on_save(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.save_state()
            from persistence import ProjectStore
            ProjectStore.upsert_project(self.editor.project)
            self.editor.show_save_feedback()

    def _on_focus_chord_name(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.focus_chord_name()

    def _on_focus_description(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.focus_description()

    def _on_dot_properties(self, event=None):
        if self.editor and self.editor.winfo_exists() and self.editor.canvas_widget:
            self.editor.canvas_widget.on_dot_properties_hotkey()

    def _on_toggle_barre(self, event=None):
        if self.editor and self.editor.winfo_exists():
            self.editor.toggle_barre()

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

        self.dashboard = None
        self.editor = EditorView(self, project, on_back_callback=self.show_dashboard)
        self.editor.pack(fill="both", expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.current_project:
            from persistence import ProjectStore
            ProjectStore.upsert_project(self.current_project)

        self.destroy()
