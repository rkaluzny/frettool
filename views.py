import customtkinter as ctk
from tkinter import messagebox, filedialog
import copy
import sys
import i18n
from constants import CONFIG, VERSION
from models import FretboardData, ProjectData
from persistence import ProjectStore
from export import ExportManager
from canvas import FretboardCanvas

def _input_dialog(parent, title, prompt, initial_value=""):
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(parent)
    if sys.platform == "darwin":
        try:
            dialog.attributes('-type', 'dialog')
        except:
            pass

    frame = ctk.CTkFrame(dialog)
    frame.pack(fill="both", expand=True, padx=25, pady=25)

    ctk.CTkLabel(frame, text=prompt, font=("Arial", 14),
                 text_color=CONFIG["colors"]["text"]).pack(anchor="w", pady=(0, 12))

    entry = ctk.CTkEntry(frame, width=320, font=("Arial", 14),
                         text_color=CONFIG["colors"]["text"])
    entry.pack(fill="x", pady=(0, 18))
    if initial_value:
        entry.insert(0, initial_value)
        entry.select_range(0, 'end')
        entry.icursor('end')
    entry.focus_set()

    result = {"value": None}

    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x")

    def on_ok():
        result["value"] = entry.get()
        dialog.destroy()

    def on_cancel():
        dialog.destroy()

    ctk.CTkButton(btn_frame, text=i18n.tr("dialogs.ok"), width=80,
                  command=on_ok).pack(side="right", padx=(6, 0))
    ctk.CTkButton(btn_frame, text=i18n.tr("dialogs.cancel"), width=80,
                  fg_color="transparent", border_width=1,
                  text_color=CONFIG["colors"]["text"],
                  command=on_cancel).pack(side="right")

    entry.bind("<Return>", lambda e: on_ok())
    entry.bind("<Escape>", lambda e: on_cancel())

    dialog.update_idletasks()
    dialog.grab_set()

    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")

    parent.wait_window(dialog)
    return result["value"]


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

        btn_rename_project = ctk.CTkButton(left, text=i18n.tr("editor.rename"), width=85, height=32, fg_color="transparent", border_width=1,
                                            text_color=CONFIG["colors"]["text"],
                                            command=self.rename_project)
        btn_rename_project.pack(side="left", padx=12)

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right")

        btn_undo = ctk.CTkButton(toolbar, text=i18n.tr("editor.undo"), width=45, height=35, command=self.undo)
        btn_undo.pack(side="left", padx=5)
        btn_redo = ctk.CTkButton(toolbar, text=i18n.tr("editor.redo"), width=45, height=35, command=self.redo)
        btn_redo.pack(side="left", padx=5)

        btn_pdf = ctk.CTkButton(toolbar, text=i18n.tr("editor.export_pdf"), width=70, height=35, fg_color="#e74c3c", command=lambda: self.export("pdf"))
        btn_pdf.pack(side="left", padx=5)

        btn_help = ctk.CTkButton(toolbar, text=i18n.tr("editor.help"), width=35, height=35,
                                 fg_color="transparent", border_width=1, text_color=CONFIG["colors"]["text"],
                                 command=self.show_help)
        btn_help.pack(side="left", padx=5)

        btn_back = ctk.CTkButton(toolbar, text=i18n.tr("editor.back_to_dashboard"), width=100, height=35,
                                 fg_color="transparent", border_width=1, text_color=CONFIG["colors"]["text"], command=self.back_to_dashboard)
        btn_back.pack(side="left", padx=15)

    def setup_main_area(self):
        main = ctk.CTkScrollableFrame(self, fg_color=CONFIG["colors"]["bg"])
        main.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
        main.grid_columnconfigure(0, weight=1)

        self.canvas_container = ctk.CTkFrame(main, fg_color="transparent")
        self.canvas_container.grid(row=0, column=0, pady=30, padx=20)

        self.title_frame = ctk.CTkFrame(self.canvas_container, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        lbl_title_hint = ctk.CTkLabel(self.title_frame, text=i18n.tr("editor.chord_scale_name"),
                                     font=("Arial", 13), text_color=CONFIG["colors"]["text_muted"])
        lbl_title_hint.pack(anchor="w")

        self.entry_title = ctk.CTkEntry(self.title_frame, placeholder_text=i18n.tr("editor.chord_scale_name_placeholder"),
                                       font=("Arial", 20, "bold"), height=45,
                                       text_color=CONFIG["colors"]["text"])
        self.entry_title.pack(fill="x", pady=(5, 0))
        self.entry_title.bind("<KeyRelease>", lambda e: self.save_state())

        self.canvas_widget = None

        self.desc_frame = ctk.CTkFrame(self.canvas_container, fg_color="transparent")
        self.desc_frame.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        lbl_desc_hint = ctk.CTkLabel(self.desc_frame, text=i18n.tr("editor.description_notes"),
                                    font=("Arial", 13), text_color=CONFIG["colors"]["text_muted"])
        lbl_desc_hint.pack(anchor="w")

        self.entry_desc = ctk.CTkTextbox(self.desc_frame, height=80, font=("Arial", 13),
                                          text_color=CONFIG["colors"]["text"])
        self.entry_desc.pack(fill="x", pady=(5, 0))
        self.entry_desc.bind("<KeyRelease>", lambda e: self.save_state())

    def setup_sidebar(self):
        sidebar = ctk.CTkScrollableFrame(self, width=280, corner_radius=0, fg_color=CONFIG["colors"]["surface"])
        sidebar.grid(row=1, column=1, sticky="ns")

        lbl = ctk.CTkLabel(sidebar, text=i18n.tr("editor.fretboards"), font=("Arial", 16, "bold"),
                           text_color=CONFIG["colors"]["text"])
        lbl.pack(pady=20, padx=20, anchor="w")

        btn_add = ctk.CTkButton(sidebar, text=i18n.tr("editor.new_fretboard"), height=40, text_color=CONFIG["colors"]["text"],
                                command=self.add_new_fretboard)
        btn_add.pack(pady=10, padx=20, fill="x")

        self.list_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.list_frame.pack(fill="x", padx=15, pady=10)
        self.refresh_list()

        settings_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        settings_frame.pack(fill="x", padx=20, pady=20)

        lbl_settings = ctk.CTkLabel(settings_frame, text=i18n.tr("editor.sidebar_settings"), font=("Arial", 14, "bold"),
                                    text_color=CONFIG["colors"]["text"])
        lbl_settings.pack(anchor="w", pady=(0, 10))

        self.btn_dot_color = ctk.CTkButton(settings_frame, text=i18n.tr("editor.dot_color"), height=34, text_color=CONFIG["colors"]["text"],
                                            command=self.pick_dot_color)
        self.btn_dot_color.pack(fill="x", pady=(0, 8))

        lbl_hint = ctk.CTkLabel(settings_frame, text=i18n.tr("editor.dot_color_hint"),
                                text_color=CONFIG["colors"]["text_muted"], font=("Arial", 10))
        lbl_hint.pack(anchor="w", pady=(0, 8))

        self.barres_disabled_var = ctk.BooleanVar(value=False)
        self.chk_disable_barres = ctk.CTkCheckBox(
            settings_frame,
            text=i18n.tr("editor.disable_barres"),
            variable=self.barres_disabled_var,
            text_color=CONFIG["colors"]["text"],
            command=self.on_barres_toggle,
        )
        self.chk_disable_barres.pack(anchor="w", pady=(0, 8))

        self.entry_strings = ctk.CTkEntry(settings_frame, placeholder_text=i18n.tr("editor.strings_placeholder"),
                                           text_color=CONFIG["colors"]["text"])
        self.entry_strings.pack(fill="x", pady=5)
        self.entry_strings.bind("<KeyRelease>", lambda e: self.save_state())

        self.entry_frets = ctk.CTkEntry(settings_frame, placeholder_text=i18n.tr("editor.frets_placeholder"),
                                         text_color=CONFIG["colors"]["text"])
        self.entry_frets.pack(fill="x", pady=5)
        self.entry_frets.bind("<KeyRelease>", lambda e: self.save_state())

        btn_del = ctk.CTkButton(sidebar, text=i18n.tr("editor.delete_fretboard"), height=40, fg_color="#e74c3c",
                               hover_color="#c0392b", text_color="#ffffff", command=self.delete_current_fretboard)
        btn_del.pack(pady=20, padx=20, fill="x")

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for i, fb in enumerate(self.project.fretboards):
            btn = ctk.CTkButton(self.list_frame, text=fb.title or i18n.tr("editor.fretboard_name", number=i+1),
                                fg_color="transparent", border_width=1, height=50,
                                anchor="w", text_color=CONFIG["colors"]["text"],
                                command=lambda f=fb: self.select_fretboard(f))
            btn.pack(fill="x", pady=3)

            lbl_count = ctk.CTkLabel(btn, text=i18n.tr("editor.notes_count", count=len(fb.positions)),
                                    font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"])
            lbl_count.place(relx=1, rely=0.5, anchor="e", x=-15)

            if self.current_fretboard == fb:
                btn.configure(fg_color=CONFIG["colors"]["accent"], text_color=CONFIG["colors"]["text"])

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

        self.barres_disabled_var.set(getattr(fb, "barres_disabled", False))

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
            if messagebox.askyesno(i18n.tr("editor.delete_fretboard_dialog.title"), i18n.tr("editor.delete_fretboard_dialog.message")):
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

        self.current_fretboard.barres_disabled = self.barres_disabled_var.get()

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

    def show_help(self):
        from constants import show_help
        show_help(self)

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

        self.barres_disabled_var.set(getattr(self.current_fretboard, "barres_disabled", False))

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
        chosen = colorchooser.askcolor(color=initial, title=i18n.tr("editor.dot_color_dialog.title"))
        if chosen and chosen[1]:
            self.current_fretboard.dot_color = chosen[1]
            self.update_dot_color_button()
            if self.canvas_widget:
                self.canvas_widget.draw()
            self.push_history()

    def on_barres_toggle(self):
        if self.current_fretboard:
            self.current_fretboard.barres_disabled = self.barres_disabled_var.get()
            if self.canvas_widget:
                self.canvas_widget.draw()
            self.push_history()

    def rename_project(self):
        new_name = _input_dialog(self, i18n.tr("editor.rename_project_dialog.title"),
                                 i18n.tr("editor.rename_project_dialog.prompt"),
                                 initial_value=self.project.name)
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
                                               filetypes=[(i18n.tr(f"export.file_dialog_{format_type}"), f".{format_type}")])
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

        btn_settings = ctk.CTkButton(header, text=i18n.tr("dashboard.settings"), height=45, font=("Arial", 14),
                                     fg_color="transparent", border_width=1,
                                     text_color=CONFIG["colors"]["text"],
                                     command=self.open_settings)
        btn_settings.pack(side="right", padx=(0, 10))

        btn_help = ctk.CTkButton(header, text=i18n.tr("dashboard.help"), height=45, font=("Arial", 14),
                                 fg_color="transparent", border_width=1,
                                 text_color=CONFIG["colors"]["text"],
                                 command=self.show_help)
        btn_help.pack(side="right", padx=(0, 10))

        btn_new = ctk.CTkButton(header, text=i18n.tr("dashboard.new_project"), height=45, font=("Arial", 14),
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
            lbl = ctk.CTkLabel(self.project_grid, text=i18n.tr("dashboard.no_projects"),
                              text_color=CONFIG["colors"]["text_muted"], font=("Arial", 16))
            lbl.pack(pady=100)
            return

        for proj in projects:
            card = ctk.CTkFrame(self.project_grid, corner_radius=20, fg_color=CONFIG["colors"]["surface"],
                               height=120)
            card.pack(fill="x", pady=15)
            card.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=30, pady=(18, 0))

            lbl_name = ctk.CTkLabel(top, text=proj.name, font=("Arial", 20, "bold"),
                                    text_color=CONFIG["colors"]["text"])
            lbl_name.pack(side="left")
            lbl_name.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

            btns = ctk.CTkFrame(top, fg_color="transparent")
            btns.pack(side="right")

            btn_rename = ctk.CTkButton(btns, text=i18n.tr("dashboard.project_card.rename"), width=80, height=32, fg_color="transparent", border_width=1,
                                       text_color=CONFIG["colors"]["text"],
                                       command=lambda p=proj: self.rename_project(p))
            btn_rename.pack(side="left", padx=(0, 8))

            btn_delete = ctk.CTkButton(btns, text=i18n.tr("dashboard.project_card.delete"), width=70, height=32, fg_color="#e74c3c", hover_color="#c0392b",
                                      command=lambda p=proj: self.delete_project(p))
            btn_delete.pack(side="left")

            lbl_date = ctk.CTkLabel(card, text=i18n.tr("dashboard.project_card.info", date=proj.created_at, count=len(proj.fretboards)),
                                   text_color=CONFIG["colors"]["text_muted"], anchor="w")
            lbl_date.pack(padx=30, pady=(0, 25), fill="x")
            lbl_date.bind("<Button-1>", lambda e, p=proj: self.on_open(p))

    def create_new_project(self):
        name = _input_dialog(self, i18n.tr("dashboard.new_project_dialog.title"),
                             i18n.tr("dashboard.new_project_dialog.prompt"))
        if name:
            new_proj = ProjectData(name)
            ProjectStore.upsert_project(new_proj)
            self.load_projects()
            self.on_open(new_proj)

    def delete_project(self, project: ProjectData):
        if messagebox.askyesno(i18n.tr("dashboard.delete_project_dialog.title"), i18n.tr("dashboard.delete_project_dialog.message", name=project.name)):
            ProjectStore.delete_project(project.id)
            self.load_projects()

    def rename_project(self, project: ProjectData):
        new_name = _input_dialog(self, i18n.tr("dashboard.rename_project_dialog.title"),
                                 i18n.tr("dashboard.rename_project_dialog.prompt"),
                                 initial_value=project.name)
        if new_name and new_name.strip():
            ProjectStore.rename_project(project.id, new_name.strip())
            self.load_projects()

    def show_help(self):
        from constants import show_help
        show_help(self)

    def _show_privacy_from_settings(self):
        from privacy import show_privacy_dialog
        show_privacy_dialog(self)

    def _check_updates_from_settings(self):
        import threading
        import customtkinter as ctk
        from updater import check_for_updates, show_up_to_date_dialog, show_update_error_dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(i18n.tr("updates.checking"))
        dialog.resizable(False, False)
        dialog.transient(self)
        if sys.platform == "darwin":
            try:
                dialog.attributes('-type', 'dialog')
            except:
                pass
        frame = ctk.CTkFrame(dialog, corner_radius=16)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text=i18n.tr("updates.checking"), font=("Arial", 14)).pack(pady=20)
        dialog.update_idletasks()
        dialog.grab_set()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        def check():
            info, error = check_for_updates()
            self.after(0, dialog.destroy)
            if error:
                self.after(0, lambda: show_update_error_dialog(self, error))
            elif info:
                self.after(0, lambda: self.master._handle_update_found(info))
            else:
                self.after(0, lambda: show_up_to_date_dialog(self))
        t = threading.Thread(target=check, daemon=True)
        t.start()
        self.wait_window(dialog)

    def open_settings(self):
        from settings import SettingsManager, DEFAULT_SETTINGS
        import customtkinter as ctk
        from constants import CONFIG

        settings = SettingsManager.load_settings()
        dialog = ctk.CTkToplevel(self)
        dialog.title(i18n.tr("settings.dialog_title"))
        dialog.geometry("650x800")
        dialog.resizable(False, False)
        dialog.transient(self)
        if sys.platform == "darwin":
            try:
                dialog.attributes('-type', 'dialog')
            except:
                pass

        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text=i18n.tr("settings.heading"), font=("Arial", 24, "bold")).pack(anchor="w", pady=(0, 20))

        # Dark mode
        dark_var = ctk.BooleanVar(value=settings.get("dark_mode", True))
        dark_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dark_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(dark_frame, text=i18n.tr("settings.dark_mode"), font=("Arial", 14, "bold")).pack(side="left")
        dark_switch = ctk.CTkSwitch(dark_frame, text="", variable=dark_var)
        dark_switch.pack(side="right")

        # Default frets
        frets_var = ctk.StringVar(value=str(settings.get("default_frets", 12)))
        frets_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frets_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(frets_frame, text=i18n.tr("settings.default_frets"), font=("Arial", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(frets_frame, text=i18n.tr("settings.default_frets_desc"), font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
        frets_entry = ctk.CTkEntry(frets_frame, textvariable=frets_var, width=100)
        frets_entry.pack(anchor="w")

        # Default string count
        strings_var = ctk.StringVar(value=str(settings.get("default_string_count", 6)))
        strings_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        strings_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(strings_frame, text=i18n.tr("settings.default_string_count"), font=("Arial", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(strings_frame, text=i18n.tr("settings.default_string_count_desc"), font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
        strings_entry = ctk.CTkEntry(strings_frame, textvariable=strings_var, width=100)
        strings_entry.pack(anchor="w")

        # Barre settings
        ctk.CTkLabel(scroll, text=i18n.tr("settings.barre_behaviour"), font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))

        barres_def_var = ctk.BooleanVar(value=settings.get("barres_enabled_default", True))
        barres_def_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        barres_def_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(barres_def_frame, text=i18n.tr("settings.barres_enabled_default"), font=("Arial", 14, "bold")).pack(side="left")
        ctk.CTkSwitch(barres_def_frame, text="", variable=barres_def_var).pack(side="right")

        min_str_var = ctk.StringVar(value=str(settings.get("barre_min_strings", 2)))
        min_str_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        min_str_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(min_str_frame, text=i18n.tr("settings.barre_min_strings"), font=("Arial", 14, "bold")).pack(anchor="w")
        ctk.CTkLabel(min_str_frame, text=i18n.tr("settings.barre_min_strings_desc"), font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(min_str_frame, textvariable=min_str_var, width=100).pack(anchor="w")

        # Dimensions
        ctk.CTkLabel(scroll, text=i18n.tr("settings.dimensions_heading"), font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))
        dim_settings = settings.get("dimensions", DEFAULT_SETTINGS["dimensions"])
        dim_entries = {}
        dim_descriptions = [
            "string_spacing", "fret_spacing", "margin_top", "margin_bottom",
            "margin_side", "nut_width", "dot_radius", "dot_small_radius",
            "marker_radius", "barre_half_width", "barre_outline_width",
            "barre_marker_radius"
        ]
        for key in dim_descriptions:
            frame = ctk.CTkFrame(scroll, fg_color="transparent")
            frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(frame, text=i18n.tr(f"settings.dimensions.{key}"), font=("Arial", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(frame, text=i18n.tr(f"settings.dimensions.{key}_desc"), font=("Arial", 11), text_color=CONFIG["colors"]["text_muted"]).pack(anchor="w", pady=(0, 5))
            var = ctk.StringVar(value=str(dim_settings.get(key, DEFAULT_SETTINGS["dimensions"][key])))
            entry = ctk.CTkEntry(frame, textvariable=var, width=120)
            entry.pack(anchor="w")
            dim_entries[key] = var

        # Preset colors
        ctk.CTkLabel(scroll, text=i18n.tr("settings.preset_colors"), font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))
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

        btn_add_color = ctk.CTkButton(scroll, text=i18n.tr("settings.add_color"), height=32, command=add_color)
        btn_add_color.pack(anchor="w", pady=(5, 15))

        # Privacy & Updates
        ctk.CTkLabel(scroll, text=i18n.tr("settings.about_heading"), font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))

        about_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        about_frame.pack(fill="x", pady=(0, 15))

        privacy_btn = ctk.CTkButton(about_frame, text=i18n.tr("settings.show_privacy"), height=38,
                                    fg_color="transparent", border_width=1,
                                    text_color=CONFIG["colors"]["text"],
                                    command=lambda: self._show_privacy_from_settings())
        privacy_btn.pack(side="left", padx=(0, 10))

        update_btn = ctk.CTkButton(about_frame, text=i18n.tr("settings.check_updates"), height=38,
                                   fg_color="transparent", border_width=1,
                                   text_color=CONFIG["colors"]["text"],
                                   command=lambda: self._check_updates_from_settings())
        update_btn.pack(side="left")

        # Language setting
        lang_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        lang_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(lang_frame, text=i18n.tr("settings.language"), font=("Arial", 14, "bold")).pack(anchor="w")
        lang_var = ctk.StringVar(value=i18n.LANGUAGE_NAMES.get(settings.get("language") or i18n.get_language(), "English"))
        lang_menu = ctk.CTkOptionMenu(lang_frame, values=list(i18n.LANGUAGE_NAMES.values()), variable=lang_var)
        lang_menu.pack(anchor="w")

        def on_lang_change(choice):
            for code, name in i18n.LANGUAGES:
                if name == choice:
                    settings["language"] = code
                    i18n.set_language(code)
                    break

        lang_menu.configure(command=on_lang_change)

        # Save button
        def save_settings():
            try:
                settings["dark_mode"] = dark_var.get()
                settings["default_frets"] = int(frets_var.get())
                settings["default_string_count"] = int(strings_var.get())
                settings["barres_enabled_default"] = barres_def_var.get()
                settings["barre_min_strings"] = max(2, int(min_str_var.get()))
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
                messagebox.showinfo(i18n.tr("settings.saved_title"), i18n.tr("settings.saved_message"))
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror(i18n.tr("dialogs.error"), str(e))

        btn_save = ctk.CTkButton(scroll, text=i18n.tr("settings.save"), height=45, font=("Arial", 14),
                                 command=save_settings)
        btn_save.pack(pady=(10, 20))

        dialog.update_idletasks()
        dialog.grab_set()
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (650 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (750 // 2)
        dialog.geometry(f"+{x}+{y}")
        self.wait_window(dialog)
