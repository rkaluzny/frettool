import customtkinter as ctk
from tkinter import messagebox, filedialog
import copy
from constants import CONFIG
from models import FretboardData, ProjectData
from persistence import ProjectStore
from export import ExportManager
from canvas import FretboardCanvas

class EditorView(ctk.CTkFrame):
    def __init__(self, parent, project: ProjectData, on_back_callback):
        super().__init__(parent)
        self.project = project
        self.on_back = on_back_callback
        self.current_fretboard: FretboardData = None
        self.history_stack = []
        self.redo_stack = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.setup_header()
        self.setup_main_area()
        self.setup_sidebar()

        if self.project.fretboards:
            self.select_fretboard(self.project.fretboards[0])
        else:
            self.add_new_fretboard()

    def on_print_shortcut(self, event=None):
        self.export("pdf")

    def setup_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(20, 10))

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")

        self.lbl_project_title = ctk.CTkLabel(left, text=self.project.name, font=("Arial", 24, "bold"))
        self.lbl_project_title.pack(side="left")

        btn_rename_project = ctk.CTkButton(left, text="Rename", width=85, height=32, fg_color="transparent", border_width=1,
                                           text_color="#000000",
                                           command=self.rename_project)
        btn_rename_project.pack(side="left", padx=12)

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right")

        btn_undo = ctk.CTkButton(toolbar, text="↶", width=45, height=35, command=self.undo)
        btn_undo.pack(side="left", padx=5)
        btn_redo = ctk.CTkButton(toolbar, text="↷", width=45, height=35, command=self.redo)
        btn_redo.pack(side="left", padx=5)

        btn_pdf = ctk.CTkButton(toolbar, text="📄 PDF", width=70, height=35, fg_color="#e74c3c", command=lambda: self.export("pdf"))
        btn_pdf.pack(side="left", padx=5)
        btn_svg = ctk.CTkButton(toolbar, text="📐 SVG", width=70, height=35, fg_color="#3498db", command=lambda: self.export("svg"))
        btn_svg.pack(side="left", padx=5)

        btn_print = ctk.CTkButton(toolbar, text="Ctrl+P Print", width=100, height=35, fg_color="#2ecc71", command=lambda: self.export("pdf"))
        btn_print.pack(side="left", padx=5)

        btn_back = ctk.CTkButton(toolbar, text="← Dashboard", width=100, height=35,
                                 fg_color="transparent", border_width=1, text_color="#000000", command=self.back_to_dashboard)
        btn_back.pack(side="left", padx=15)

    def setup_main_area(self):
        main = ctk.CTkScrollableFrame(self, fg_color=CONFIG["colors"]["bg"])
        main.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        main.grid_columnconfigure(0, weight=1)

        self.canvas_container = ctk.CTkFrame(main, fg_color="transparent")
        self.canvas_container.grid(row=0, column=0, pady=30, padx=20)

        self.title_frame = ctk.CTkFrame(self.canvas_container, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        lbl_title_hint = ctk.CTkLabel(self.title_frame, text="Akkord / Skala Name",
                                     font=("Arial", 13), text_color=CONFIG["colors"]["text_muted"])
        lbl_title_hint.pack(anchor="w")

        self.entry_title = ctk.CTkEntry(self.title_frame, placeholder_text="z.B. C-Dur oder A-Moll Pentatonik",
                                       font=("Arial", 20, "bold"), height=45)
        self.entry_title.pack(fill="x", pady=(5, 0))
        self.entry_title.bind("<KeyRelease>", lambda e: self.save_state())

        self.canvas_widget = None

        self.desc_frame = ctk.CTkFrame(self.canvas_container, fg_color="transparent")
        self.desc_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        lbl_desc_hint = ctk.CTkLabel(self.desc_frame, text="Beschreibung / Notizen",
                                    font=("Arial", 13), text_color=CONFIG["colors"]["text_muted"])
        lbl_desc_hint.pack(anchor="w")

        self.entry_desc = ctk.CTkTextbox(self.desc_frame, height=80, font=("Arial", 13))
        self.entry_desc.pack(fill="x", pady=(5, 0))
        self.entry_desc.bind("<KeyRelease>", lambda e: self.save_state())

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=CONFIG["colors"]["surface"])
        sidebar.grid(row=1, column=1, sticky="ns")

        lbl = ctk.CTkLabel(sidebar, text="Fretboards", font=("Arial", 16, "bold"))
        lbl.pack(pady=20, padx=20, anchor="w")

        btn_add = ctk.CTkButton(sidebar, text="+ Neues Fretboard", height=40, command=self.add_new_fretboard)
        btn_add.pack(pady=10, padx=20, fill="x")

        self.list_frame = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.refresh_list()

        settings_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=20)

        lbl_settings = ctk.CTkLabel(settings_frame, text="Einstellungen", font=("Arial", 14, "bold"))
        lbl_settings.pack(anchor="w", pady=(0, 10))

        self.btn_dot_color = ctk.CTkButton(settings_frame, text="Dot color", height=34, command=self.pick_dot_color)
        self.btn_dot_color.pack(fill="x", pady=(0, 8))

        lbl_hint = ctk.CTkLabel(settings_frame, text="Right click: toggle X markers\nCtrl+click: square dot\nShift+click: triangle dot\nAlt+click: smaller dot",
                                text_color=CONFIG["colors"]["text_muted"], font=("Arial", 10))
        lbl_hint.pack(anchor="w", pady=(0, 8))

        self.entry_strings = ctk.CTkEntry(settings_frame, placeholder_text="Saiten (z.B. 6)")
        self.entry_strings.pack(fill="x", pady=5)
        self.entry_strings.bind("<KeyRelease>", lambda e: self.save_state())

        self.entry_frets = ctk.CTkEntry(settings_frame, placeholder_text="Anzahl Bünde (z.B. 12)")
        self.entry_frets.pack(fill="x", pady=5)
        self.entry_frets.bind("<KeyRelease>", lambda e: self.save_state())

        btn_del = ctk.CTkButton(sidebar, text="🗑 Fretboard löschen", height=40, fg_color="#e74c3c",
                               hover_color="#c0392b", command=self.delete_current_fretboard)
        btn_del.pack(pady=20, padx=20, fill="x")

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for i, fb in enumerate(self.project.fretboards):
            btn = ctk.CTkButton(self.list_frame, text=fb.title or f"Fretboard {i+1}",
                                fg_color="transparent", border_width=1, height=50,
                                anchor="w",
                                command=lambda f=fb: self.select_fretboard(f))
            btn.pack(fill="x", pady=3)

            lbl_count = ctk.CTkLabel(btn, text=f"{len(fb.positions)} Noten",
                                    font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"])
            lbl_count.place(relx=1, rely=0.5, anchor="e", x=-15)

            if self.current_fretboard == fb:
                btn.configure(fg_color=CONFIG["colors"]["accent"], text_color="#000000")

    def select_fretboard(self, fb: FretboardData):
        self.save_state()
        self.current_fretboard = fb

        self.entry_title.delete(0, 'end')
        self.entry_title.insert(0, fb.title)

        self.entry_desc.delete("0.0", "end")
        self.entry_desc.insert("0.0", fb.description)

        self.entry_frets.delete(0, 'end')
        self.entry_frets.insert(0, str(fb.num_frets))

        self.entry_strings.delete(0, 'end')
        self.entry_strings.insert(0, str(getattr(fb, "string_count", CONFIG["string_count"])))

        if self.canvas_widget:
            self.canvas_widget.destroy()

        self.canvas_widget = FretboardCanvas(self.canvas_container, fb, on_change_callback=lambda: self.push_history())
        self.canvas_widget.grid(row=1, column=0, pady=(5, 20))
        self.update_dot_color_button()

        self.refresh_list()

    def add_new_fretboard(self):
        self.save_state()
        new_fb = FretboardData()
        self.project.fretboards.append(new_fb)
        self.select_fretboard(new_fb)

    def delete_current_fretboard(self):
        if self.current_fretboard in self.project.fretboards:
            if messagebox.askyesno("Löschen", "Dieses Fretboard wirklich löschen?"):
                self.project.fretboards.remove(self.current_fretboard)
                self.current_fretboard = None
                if self.project.fretboards:
                    self.select_fretboard(self.project.fretboards[0])
                else:
                    if self.canvas_widget: self.canvas_widget.destroy()
                self.refresh_list()

    def save_state(self):
        if not self.current_fretboard: return

        self.current_fretboard.title = self.entry_title.get().strip()
        self.current_fretboard.description = self.entry_desc.get("0.0", "end").strip()

        try:
            sc = int(self.entry_strings.get())
            if 2 <= sc <= 12:
                old_sc = getattr(self.current_fretboard, "string_count", CONFIG["string_count"])
                self.current_fretboard.string_count = sc
                if old_sc != sc:
                    self.current_fretboard.positions = set((s, f) for (s, f) in self.current_fretboard.positions if s < sc)
                    self.current_fretboard.x_positions = set((s, f) for (s, f) in self.current_fretboard.x_positions if s < sc)

                    if getattr(self.current_fretboard, "dot_texts", None):
                        for k in list(self.current_fretboard.dot_texts.keys()):
                            try:
                                s = int(k.split(",")[0])
                                if s >= sc:
                                    self.current_fretboard.dot_texts.pop(k, None)
                            except Exception:
                                pass
                    if getattr(self.current_fretboard, "dot_colors", None):
                        for k in list(self.current_fretboard.dot_colors.keys()):
                            try:
                                s = int(k.split(",")[0])
                                if s >= sc:
                                    self.current_fretboard.dot_colors.pop(k, None)
                            except Exception:
                                pass

                    if self.canvas_widget:
                        self.canvas_widget.update_dimensions()
        except: pass

        try:
            val = int(self.entry_frets.get())
            if 0 < val <= 24:
                old = self.current_fretboard.num_frets
                self.current_fretboard.num_frets = val
                if self.canvas_widget and old != val:
                    self.canvas_widget.update_dimensions()
        except: pass

    def push_history(self):
        if self.current_fretboard:
            self.history_stack.append(copy.deepcopy(self.current_fretboard))
            if len(self.history_stack) > 20:
                self.history_stack.pop(0)
            self.redo_stack.clear()
            ProjectStore.upsert_project(self.project)

    def undo(self):
        if self.history_stack:
            self.redo_stack.append(copy.deepcopy(self.current_fretboard))
            prev = self.history_stack.pop()
            self.restore_fretboard(prev)

    def redo(self):
        if self.redo_stack:
            self.history_stack.append(copy.deepcopy(self.current_fretboard))
            next_state = self.redo_stack.pop()
            self.restore_fretboard(next_state)

    def restore_fretboard(self, fb_data):
        self.current_fretboard.title = fb_data.title
        self.current_fretboard.description = fb_data.description
        self.current_fretboard.num_frets = fb_data.num_frets
        self.current_fretboard.string_count = getattr(fb_data, "string_count", CONFIG["string_count"])
        self.current_fretboard.positions = fb_data.positions
        self.current_fretboard.dot_color = getattr(fb_data, "dot_color", CONFIG["colors"]["dot"])
        self.current_fretboard.x_positions = getattr(fb_data, "x_positions", set()) or set()
        self.current_fretboard.dot_texts = getattr(fb_data, "dot_texts", {}) or {}
        self.current_fretboard.dot_colors = getattr(fb_data, "dot_colors", {}) or {}
        self.current_fretboard.dot_types = getattr(fb_data, "dot_types", {}) or {}
        self.current_fretboard.dot_small = getattr(fb_data, "dot_small", {}) or {}

        self.entry_title.delete(0, 'end')
        self.entry_title.insert(0, fb_data.title)

        self.entry_desc.delete("0.0", "end")
        self.entry_desc.insert("0.0", fb_data.description)

        self.entry_frets.delete(0, 'end')
        self.entry_frets.insert(0, str(fb_data.num_frets))

        self.entry_strings.delete(0, 'end')
        self.entry_strings.insert(0, str(getattr(fb_data, "string_count", CONFIG["string_count"])))

        if self.canvas_widget: self.canvas_widget.destroy()
        self.canvas_widget = FretboardCanvas(self.canvas_container, self.current_fretboard, on_change_callback=lambda: self.push_history())
        self.canvas_widget.grid(row=1, column=0, pady=(5, 20))
        self.update_dot_color_button()
        self.refresh_list()

    def update_dot_color_button(self):
        if not getattr(self, "btn_dot_color", None):
            return
        if not self.current_fretboard:
            self.btn_dot_color.configure(fg_color=CONFIG["colors"]["surface"])
            return
        color = self.current_fretboard.dot_color or CONFIG["colors"]["dot"]
        self.btn_dot_color.configure(fg_color=color, hover_color=color)

    def pick_dot_color(self):
        if not self.current_fretboard:
            return
        from tkinter import colorchooser
        initial = self.current_fretboard.dot_color or CONFIG["colors"]["dot"]
        chosen = colorchooser.askcolor(color=initial, title="Choose dot color")
        if chosen and chosen[1]:
            self.current_fretboard.dot_color = chosen[1]
            self.update_dot_color_button()
            if self.canvas_widget:
                self.canvas_widget.draw()
            self.push_history()

    def rename_project(self):
        dialog = ctk.CTkInputDialog(text="Projektname:", title="Projekt umbenennen")
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            self.project.name = new_name.strip()
            self.lbl_project_title.configure(text=self.project.name)
            ProjectStore.upsert_project(self.project)

    def back_to_dashboard(self):
        self.save_state()
        ProjectStore.upsert_project(self.project)
        self.on_back()

    def export(self, format_type):
        if not self.current_fretboard: return
        filename = filedialog.asksaveasfilename(defaultextension=f".{format_type}",
                                               filetypes=[(f"{format_type.upper()} files", f".{format_type}")])
        if filename:
            if format_type == "svg":
                ExportManager.export_svg(self.current_fretboard, filename)
            elif format_type == "pdf":
                ExportManager.export_pdf(self.project, filename)


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, on_open_project_callback):
        super().__init__(parent)
        self.on_open = on_open_project_callback

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=50, pady=30)

        lbl_title = ctk.CTkLabel(header, text=CONFIG["app_name"],
                                 font=("Arial", 40, "bold"), text_color=CONFIG["colors"]["accent"])
        lbl_title.pack(side="left")

        btn_settings = ctk.CTkButton(header, text="⚙ Settings", height=45, font=("Arial", 14),
                                     fg_color="transparent", border_width=1,
                                     text_color="#000000",
                                     command=self.open_settings)
        btn_settings.pack(side="right", padx=(0, 10))

        btn_new = ctk.CTkButton(header, text="+ Neues Projekt", height=45, font=("Arial", 14),
                                command=self.create_new_project)
        btn_new.pack(side="right")

        self.project_grid = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.project_grid.grid(row=1, column=0, sticky="nsew", padx=50, pady=20)

        self.load_projects()

    def load_projects(self):
        for widget in self.project_grid.winfo_children():
            widget.destroy()

        projects = ProjectStore.load_projects()
        if not projects:
            lbl = ctk.CTkLabel(self.project_grid, text="Keine Projekte gefunden.\nErstelle dein erstes Projekt!",
                              text_color="gray", font=("Arial", 16))
            lbl.pack(pady=100)
            return

        for proj in projects:
            card = ctk.CTkFrame(self.project_grid, corner_radius=20, fg_color=CONFIG["colors"]["surface"],
                               height=120)
            card.pack(fill="x", pady=15)
            card.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=30, pady=(18, 0))

            lbl_name = ctk.CTkLabel(top, text=proj.name, font=("Arial", 20, "bold"))
            lbl_name.pack(side="left")
            lbl_name.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

            btns = ctk.CTkFrame(top, fg_color="transparent")
            btns.pack(side="right")

            btn_rename = ctk.CTkButton(btns, text="Rename", width=80, height=32, fg_color="transparent", border_width=1,
                                       text_color="#000000",
                                       command=lambda p=proj: self.rename_project(p))
            btn_rename.pack(side="left", padx=(0, 8))

            btn_delete = ctk.CTkButton(btns, text="Delete", width=70, height=32, fg_color="#e74c3c", hover_color="#c0392b",
                                      command=lambda p=proj: self.delete_project(p))
            btn_delete.pack(side="left")

            lbl_date = ctk.CTkLabel(card, text=f"📅 {proj.created_at}  •  🎸 {len(proj.fretboards)} Fretboards",
                                   text_color=CONFIG["colors"]["text_muted"], anchor="w")
            lbl_date.pack(padx=30, pady=(0, 25), fill="x")
            lbl_date.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

    def create_new_project(self):
        dialog = ctk.CTkInputDialog(text="Projektname:", title="Neues Projekt")
        name = dialog.get_input()
        if name:
            new_proj = ProjectData(name)
            ProjectStore.upsert_project(new_proj)
            self.load_projects()
            self.on_open(new_proj)

    def delete_project(self, project: ProjectData):
        if messagebox.askyesno("Löschen", f"Projekt '{project.name}' wirklich löschen?"):
            ProjectStore.delete_project(project.id)
            self.load_projects()

    def rename_project(self, project: ProjectData):
        dialog = ctk.CTkInputDialog(text="Neuer Projektname:", title="Projekt umbenennen")
        new_name = dialog.get_input()
        if new_name and new_name.strip():
            ProjectStore.rename_project(project.id, new_name.strip())
            self.load_projects()

    def open_settings(self):
        from settings import SettingsManager, DEFAULT_SETTINGS
        import customtkinter as ctk
        from constants import CONFIG, PRESET_COLORS

        settings = SettingsManager.load_settings()
        dialog = ctk.CTkToplevel(self)
        dialog.title("Settings")
        dialog.geometry("650x750")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text="Settings", font=("Arial", 24, "bold")).pack(anchor="w", pady=(0, 20))

        # Dark mode
        dark_var = ctk.BooleanVar(value=settings.get("dark_mode", True))
        dark_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dark_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(dark_frame, text="Dark Mode", font=("Arial", 14, "bold")).pack(side="left")
        dark_switch = ctk.CTkSwitch(dark_frame, text="", variable=dark_var)
        dark_switch.pack(side="right")

        # Default frets
        frets_var = ctk.StringVar(value=str(settings.get("default_frets", 12)))
        frets_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frets_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(frets_frame, text="Default Frets", font=("Arial", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(frets_frame, text="Number of frets for new fretboards (1-24)", font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
        frets_entry = ctk.CTkEntry(frets_frame, textvariable=frets_var, width=100)
        frets_entry.pack(anchor="w")

        # Default string count
        strings_var = ctk.StringVar(value=str(settings.get("default_string_count", 6)))
        strings_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        strings_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(strings_frame, text="Default String Count", font=("Arial", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(strings_frame, text="Number of strings for new fretboards (2-12)", font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
        strings_entry = ctk.CTkEntry(strings_frame, textvariable=strings_var, width=100)
        strings_entry.pack(anchor="w")

        # Dimensions
        ctk.CTkLabel(scroll, text="Dimensions", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))
        dim_settings = settings.get("dimensions", DEFAULT_SETTINGS["dimensions"])
        dim_entries = {}
        dim_descriptions = {
            "string_spacing": "Vertical space between strings (pixels)",
            "fret_spacing": "Horizontal space between frets (pixels)",
            "margin_top": "Top margin (pixels)",
            "margin_bottom": "Bottom margin (pixels)",
            "margin_side": "Side margin (pixels)",
            "nut_width": "Width of nut line (pixels)",
            "dot_radius": "Radius of normal dots (pixels)",
            "dot_small_radius": "Radius of small dots (pixels)",
            "marker_radius": "Radius of fret markers (pixels)"
        }
        for key, desc in dim_descriptions.items():
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(frame, text=key.replace("_", " ").title(), font=("Arial", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(frame, text=desc, font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
            var = ctk.StringVar(value=str(dim_settings.get(key, DEFAULT_SETTINGS["dimensions"][key])))
            entry = ctk.CTkEntry(frame, textvariable=var, width=120)
            entry.pack(anchor="w")
            dim_entries[key] = var

        # Preset colors
        ctk.CTkLabel(scroll, text="Preset Colors (for mouse wheel)", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))
        preset_colors = settings.get("preset_colors", DEFAULT_SETTINGS["preset_colors"])
        color_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        color_frame.pack(fill="x", pady=(0, 10))
        color_vars = []
        def add_color():
            settings["preset_colors"].append("#000000")
            refresh_colors()
        def remove_color(idx):
            if len(settings["preset_colors"]) > 1:
                settings["preset_colors"].pop(idx)
                refresh_colors()
        def refresh_colors():
            for widget in color_frame.winfo_children():
                widget.destroy()
            color_vars.clear()
            for i, color in enumerate(settings["preset_colors"]):
                row = ctk.CTkFrame(color_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)
                var = ctk.StringVar(value=color)
                color_vars.append(var)
                entry = ctk.CTkEntry(row, textvariable=var, width=120)
                entry.pack(side="left", padx=(0, 10))

                def update_preview(var=var, btn=None):
                    color_val = var.get()
                    try:
                        btn.configure(fg_color=color_val, hover_color=color_val)
                    except:
                        pass

                btn = ctk.CTkButton(row, text=" ", width=30, fg_color=color, hover_color=color)
                btn.pack(side="left", padx=(0, 10))
                var.trace_add("write", lambda *args, btn=btn, var=var: update_preview(var, btn))
                btn_rem = ctk.CTkButton(row, text="✕", width=30, fg_color="#e74c3c", hover_color="#c0392b",
                                         command=lambda idx=i: remove_color(idx))
                btn_rem.pack(side="left")
        refresh_colors()

        btn_add_color = ctk.CTkButton(scroll, text="+ Add Color", height=32, command=add_color)
        btn_add_color.pack(anchor="w", pady=(5, 15))

        # Save button
        def save_settings():
            try:
                settings["dark_mode"] = dark_var.get()
                settings["default_frets"] = int(frets_var.get())
                settings["default_string_count"] = int(strings_var.get())
                dims = {}
                for key, var in dim_entries.items():
                    dims[key] = int(var.get())
                settings["dimensions"] = dims
                new_colors = []
                for var in color_vars:
                    val = var.get().strip()
                    if val and val.startswith("#") and len(val) == 7:
                        new_colors.append(val)
                if new_colors:
                    settings["preset_colors"] = new_colors
                SettingsManager.save_settings(settings)
                SettingsManager.apply_to_config()
                dialog.destroy()
                from tkinter import messagebox
                messagebox.showinfo("Settings", "Settings saved. Restart may be required for some changes.")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", str(e))

        btn_save = ctk.CTkButton(scroll, text="Save Settings", height=45, font=("Arial", 14),
                                 command=save_settings)
        btn_save.pack(pady=(10, 20))

        dialog.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (650 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (750 // 2)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
