import os
import sys
import customtkinter as ctk
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
        from constants import CONFIG
        self.title(CONFIG["app_name"])
        self.geometry("1400x900")
        self.minsize(1200, 700)
        self.current_project: ProjectData = None
        self.editor = None

        # Bind Ctrl+P for printing globally
        self.bind("<Control-p>", self.on_print_shortcut)

        self.show_dashboard()

    def on_print_shortcut(self, event=None):
        """Handle Ctrl+P shortcut to print PDF"""
        if self.editor and self.editor.winfo_exists():
            self.editor.export("pdf")

    def show_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()
        
        self.editor = None  # Clear editor reference
        
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
