import customtkinter as ctk
import tkinter as tk
from constants import CONFIG, FRET_MARKERS, hex_to_rgb01, apply_symbol_map, PRESET_COLORS
from models import FretboardData
from barre_utils import get_barre_groups, get_preview_barre_groups, BarreGroup

class FretboardCanvas(ctk.CTkCanvas):
    def __init__(self, parent, fretboard_data: FretboardData, on_change_callback):
        super().__init__(parent, bg=CONFIG["colors"]["bg"], highlightthickness=0)
        self.data = fretboard_data
        self.on_change = on_change_callback
        self.hovered_pos = None
        self.hovered_xpos = None
        self.hovered_barre_key = None
        self.selected_barre_key = None
        self.hitboxes = []
        self.x_hitboxes = []
        self.barre_hitboxes = []
        self.grid_hover = None  # (string, fret) where mouse is hovering on empty grid

        base_frets = max(CONFIG["default_frets"], self.data.num_frets)
        self.required_width = CONFIG["dimensions"]["margin_side"] * 2 + base_frets * CONFIG["dimensions"]["fret_spacing"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))
        self.required_height = CONFIG["dimensions"]["margin_top"] + CONFIG["dimensions"]["margin_bottom"] + (string_count - 1) * CONFIG["dimensions"]["string_spacing"]

        self.configure(width=self.required_width, height=self.required_height)

        self.bind("<Configure>", self.on_resize)
        self.bind("<Motion>", self.on_motion)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Double-1>", self.on_double_click)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Button-3>", self.on_right_click)
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.bind("<Up>", self.on_barre_edge_key)
        self.bind("<Down>", self.on_barre_edge_key)
        self.draw()

    def on_resize(self, event):
        self.draw()

    def update_dimensions(self):
        base_frets = max(CONFIG["default_frets"], self.data.num_frets)
        self.required_width = CONFIG["dimensions"]["margin_side"] * 2 + base_frets * CONFIG["dimensions"]["fret_spacing"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))
        self.required_height = CONFIG["dimensions"]["margin_top"] + CONFIG["dimensions"]["margin_bottom"] + (string_count - 1) * CONFIG["dimensions"]["string_spacing"]
        self.configure(width=self.required_width, height=self.required_height)
        self.draw()

    def _barre_group_lookup(self, groups):
        return {group.key: group for group in groups}

    def _find_hitbox(self, hitboxes, x, y):
        for hb in hitboxes:
            x1, y1, x2, y2 = hb["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return hb
        return None

    def _barre_geometry(self, group: BarreGroup, margin_x, margin_y_top, fret_w, string_h):
        cx = margin_x + (group.fret - 0.5) * fret_w
        half_width = max(14, int(CONFIG["dimensions"]["dot_radius"] * 1.35))
        cap_diameter = half_width * 2
        top_string_y = margin_y_top + group.start_string * string_h
        bottom_string_y = margin_y_top + group.end_string * string_h
        top = top_string_y - half_width
        bottom = bottom_string_y + half_width
        left = cx - half_width
        right = cx + half_width
        return {
            "cx": cx,
            "left": left,
            "right": right,
            "top": top,
            "bottom": bottom,
            "cap_diameter": cap_diameter,
            "half_width": half_width,
            "center_y": (top_string_y + bottom_string_y) / 2,
            "top_string_y": top_string_y,
            "bottom_string_y": bottom_string_y,
        }

    def _barre_hit_rect(self, group: BarreGroup, margin_x, margin_y_top, fret_w, string_h):
        geom = self._barre_geometry(group, margin_x, margin_y_top, fret_w, string_h)
        x_pad = max(18, int(fret_w * 0.22))
        y_pad = max(14, int(string_h * 0.22))
        return (
            geom["left"] - x_pad,
            geom["top"] - y_pad,
            geom["right"] + x_pad,
            geom["bottom"] + y_pad,
        )

    def _draw_barre(self, group: BarreGroup, margin_x, margin_y_top, fret_w, string_h, fill_color, outline_color, selected=False, hovered=False, preview=False):
        geom = self._barre_geometry(group, margin_x, margin_y_top, fret_w, string_h)
        left = geom["left"]
        right = geom["right"]
        top = geom["top"]
        bottom = geom["bottom"]
        half_width = geom["half_width"]
        cap_diameter = geom["cap_diameter"]

        body_width = 3 if selected else 2
        body_outline = outline_color
        body_fill = fill_color
        if preview:
            body_width = 1
        fill_stipple = "gray50" if preview else ""

        # Central shaft
        if bottom - top > cap_diameter:
            self.create_rectangle(
                left, top + half_width,
                right, bottom - half_width,
                fill=body_fill,
                stipple=fill_stipple,
                outline=body_outline if selected or hovered else "",
                width=body_width,
            )

        # Rounded ends
        self.create_oval(left, top, right, top + cap_diameter, fill=body_fill,
                         stipple=fill_stipple,
                         outline=body_outline if selected or hovered else "", width=body_width)
        self.create_oval(left, bottom - cap_diameter, right, bottom, fill=body_fill,
                         stipple=fill_stipple,
                         outline=body_outline if selected or hovered else "", width=body_width)

        # Subtle highlight for selected or hovered states.
        if selected or hovered:
            glow_color = outline_color if selected else fill_color
            glow_width = 4 if selected else 2
            self.create_oval(left - 1, top - 1, right + 1, bottom + 1, fill="", outline=glow_color, width=glow_width)

        self.barre_hitboxes.append({
            "rect": self._barre_hit_rect(group, margin_x, margin_y_top, fret_w, string_h),
            "key": group.key,
            "group": group,
        })

        marker_radius = max(3, CONFIG["dimensions"]["dot_radius"] // 5)
        marker_outline = "#ffffff"
        for string_idx in group.strings:
            cy = margin_y_top + string_idx * string_h
            if preview:
                marker_fill = fill_color
                marker_outline = fill_color
            else:
                marker_fill = fill_color
            self.create_oval(
                geom["cx"] - marker_radius, cy - marker_radius,
                geom["cx"] + marker_radius, cy + marker_radius,
                fill=marker_fill,
                stipple=fill_stipple,
                outline=marker_outline,
                width=1,
            )

            label = (group.labels.get(string_idx, "") or "").strip()[:2]
            if label:
                from constants import apply_symbol_map, hex_to_rgb01
                label = apply_symbol_map(label)
                r, g, b = hex_to_rgb01(fill_color)
                luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                text_color = "#0f172a" if luminance > 0.62 else "#ffffff"
                font_size = 9 if len(label) > 1 else 11
                label_y = cy - 1
                if bottom - top < 34:
                    label_y = cy + 10
                self.create_text(geom["cx"], label_y, text=label, fill=text_color, font=("Arial", font_size, "bold"))

    def _remove_note_and_recompute_barre(self, s, f):
        key = f"{s},{f}"
        self.data.positions.discard((s, f))
        if hasattr(self.data, "dot_texts") and self.data.dot_texts:
            self.data.dot_texts.pop(key, None)
        if hasattr(self.data, "dot_colors") and self.data.dot_colors:
            self.data.dot_colors.pop(key, None)
        if hasattr(self.data, "dot_types") and self.data.dot_types:
            self.data.dot_types.pop(key, None)
        if hasattr(self.data, "dot_small") and self.data.dot_small:
            self.data.dot_small.pop(key, None)
        if hasattr(self.data, "barre_excluded") and self.data.barre_excluded:
            self.data.barre_excluded.discard((s, f))

        groups = get_barre_groups(self.data)
        self.selected_barre_key = None
        for group in groups:
            if group.fret == f:
                self.selected_barre_key = group.key
                break

    def _is_note_part_of_barre(self, pos, groups):
        if not pos:
            return None
        s, f = pos
        for group in groups:
            if group.fret == f and s in group.strings:
                return group
        return None

    def get_grid_position(self, event_x, event_y):
        """Calculate which (string, fret) position the mouse is over"""
        margin_x = CONFIG["dimensions"]["margin_side"]
        margin_y_top = CONFIG["dimensions"]["margin_top"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))

        w = self.winfo_width()
        h = self.winfo_height()

        if w < 100 or h < 100:
            return None

        fret_w = (w - 2 * margin_x) / self.data.num_frets
        string_h = (h - margin_y_top - CONFIG["dimensions"]["margin_bottom"]) / (string_count - 1)

        # Check if in X marker area (left of margin)
        if event_x <= margin_x - 10:
            s_idx = int((event_y - margin_y_top) / string_h)
            if 0 <= s_idx < string_count:
                return (s_idx, 0)

        # Check if in fretboard area
        if event_x < margin_x or event_x > w - margin_x:
            return None

        s_idx = int((event_y - margin_y_top) / string_h)
        f_idx = int((event_x - margin_x) / fret_w) + 1

        if 0 <= s_idx < string_count and 1 <= f_idx <= self.data.num_frets:
            return (s_idx, f_idx)

        return None

    def on_motion(self, event):
        old_hovered_dot = self.hovered_pos
        old_hovered_x = self.hovered_xpos
        old_hovered_barre = self.hovered_barre_key
        old_grid_hover = self.grid_hover

        self.hovered_pos = None
        self.hovered_xpos = None
        self.hovered_barre_key = None
        self.grid_hover = None

        # Barres should take precedence over individual note hover states.
        barre_hit = self._find_hitbox(self.barre_hitboxes, event.x, event.y)
        if barre_hit:
            self.hovered_barre_key = barre_hit["key"]

        # Check if hovering over existing dot
        for hb in self.hitboxes:
            x1, y1, x2, y2 = hb['rect']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if self.hovered_barre_key is None or hb.get("barre_key") == self.hovered_barre_key:
                    self.hovered_pos = hb['pos']
                break

        # Check if hovering over X marker
        if self.hovered_pos is None and self.hovered_barre_key is None:
            for hb in self.x_hitboxes:
                x1, y1, x2, y2 = hb['rect']
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self.hovered_xpos = hb['pos']
                    break

        # Calculate grid hover position (where a new dot would be placed)
        if self.hovered_pos is None and self.hovered_xpos is None and self.hovered_barre_key is None:
            self.grid_hover = self.get_grid_position(event.x, event.y)

        if (old_hovered_dot != self.hovered_pos) or (old_hovered_x != self.hovered_xpos) or (old_hovered_barre != self.hovered_barre_key) or (old_grid_hover != self.grid_hover):
            self.draw()
            self.configure(cursor="hand2" if (self.hovered_pos or self.hovered_xpos or self.hovered_barre_key or self.grid_hover) else "arrow")

    def on_leave(self, event):
        self.hovered_pos = None
        self.hovered_xpos = None
        self.hovered_barre_key = None
        self.grid_hover = None
        self.draw()
        self.configure(cursor="arrow")

    def on_mousewheel(self, event):
        """Handle mousewheel to cycle through preset colors on hovered dot"""
        if self.hovered_pos is None:
            return

        s, f = self.hovered_pos
        key = f"{s},{f}"

        # Get current color index
        current_color = (getattr(self.data, "dot_colors", {}) or {}).get(key, self.data.dot_color)
        if current_color in PRESET_COLORS:
            idx = PRESET_COLORS.index(current_color)
        else:
            idx = 0

        # Determine direction (Windows uses event.delta)
        delta = event.delta
        if delta > 0:
            new_idx = (idx + 1) % len(PRESET_COLORS)
        else:
            new_idx = (idx - 1) % len(PRESET_COLORS)

        # Update color
        if not hasattr(self.data, "dot_colors") or self.data.dot_colors is None:
            self.data.dot_colors = {}
        self.data.dot_colors[key] = PRESET_COLORS[new_idx]

        self.draw()
        self.on_change()

    def on_barre_edge_key(self, event):
        if not self.hovered_barre_key and not self.selected_barre_key:
            return

        key = self.hovered_barre_key or self.selected_barre_key
        barre_group = None
        for hb in self.barre_hitboxes:
            if hb["key"] == key:
                barre_group = hb["group"]
                break

        if barre_group is None or not self.hovered_pos:
            return

        s, f = self.hovered_pos
        strings = barre_group.strings
        try:
            idx = strings.index(s)
        except ValueError:
            return

        if event.keysym == "Up":
            if idx == 0:
                return
            target_s = strings[idx - 1]
        else:
            if idx == len(strings) - 1:
                return
            target_s = strings[idx + 1]

        target_pos = (target_s, f)

        if target_pos not in self.data.positions:
            return

        if not hasattr(self.data, "barre_excluded") or self.data.barre_excluded is None:
            self.data.barre_excluded = set()

        if target_pos in self.data.barre_excluded:
            self.data.barre_excluded.discard(target_pos)
        else:
            self.data.barre_excluded.add(target_pos)

        self.selected_barre_key = None
        self.draw()
        self.on_change()

    def draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()

        if w < 100 or h < 100:
            return

        margin_x = CONFIG["dimensions"]["margin_side"]
        margin_y_top = CONFIG["dimensions"]["margin_top"]
        margin_y_bottom = CONFIG["dimensions"]["margin_bottom"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))

        fret_w = (w - 2 * margin_x) / self.data.num_frets
        string_h = (h - margin_y_top - margin_y_bottom) / (string_count - 1)

        self.create_rectangle(
            margin_x - 10, margin_y_top - 10,
            w - margin_x + 10, h - margin_y_bottom + 10,
            fill=CONFIG["colors"]["surface"], outline=""
        )

        # Draw grid hover preview
        if self.grid_hover:
            if not get_preview_barre_groups(self.data, self.grid_hover):
                s, f = self.grid_hover
                if f == 0:
                    cx = margin_x - 25
                    cy = margin_y_top + s * string_h
                    radius = 11
                else:
                    cx = margin_x + (f - 0.5) * fret_w
                    cy = margin_y_top + s * string_h
                    radius = CONFIG["dimensions"]["dot_radius"]

                # Draw preview dot (semi-transparent effect using lighter color)
                self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                               fill=CONFIG["colors"]["dot_hover"], outline="", stipple="gray50")
                self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                               outline="#ffffff", width=2)

        for i in range(string_count):
            y = margin_y_top + i * string_h
            width = 2 + (i * 0.6)
            self.create_line(margin_x, y, w - margin_x, y,
                           fill=CONFIG["colors"]["string"], width=width, capstyle="round")

        for i in range(self.data.num_frets + 1):
            x = margin_x + i * fret_w
            width = CONFIG["dimensions"]["nut_width"] if i == 0 else 3
            color = CONFIG["colors"]["nut"] if i == 0 else CONFIG["colors"]["fret_line"]
            self.create_line(x, margin_y_top, x, h - margin_y_bottom,
                           fill=color, width=width)

            if i > 0 and i % 2 == 0:
                self.create_text(x - fret_w/2, h - 25, text=str(i),
                               fill=CONFIG["colors"]["text_muted"], font=("Arial", 11, "bold"))

        for fret_num, dot_count in FRET_MARKERS.items():
            if fret_num <= self.data.num_frets:
                x = margin_x + (fret_num - 0.5) * fret_w
                if dot_count == 1:
                    y = margin_y_top + (string_count - 1) * string_h / 2
                    self.create_oval(x - CONFIG["dimensions"]["marker_radius"],
                                   y - CONFIG["dimensions"]["marker_radius"],
                                   x + CONFIG["dimensions"]["marker_radius"],
                                   y + CONFIG["dimensions"]["marker_radius"],
                                   fill=CONFIG["colors"]["marker"], outline="")
                else:
                    y1 = margin_y_top + (string_count - 1) * string_h * 0.3
                    y2 = margin_y_top + (string_count - 1) * string_h * 0.7
                    for y in [y1, y2]:
                        self.create_oval(x - CONFIG["dimensions"]["marker_radius"],
                                       y - CONFIG["dimensions"]["marker_radius"],
                                       x + CONFIG["dimensions"]["marker_radius"],
                                       y + CONFIG["dimensions"]["marker_radius"],
                                       fill=CONFIG["colors"]["marker"], outline="")

        for fret_num, label_text in self.data.labels.items():
            if 0 < fret_num <= self.data.num_frets:
                x = margin_x + (fret_num - 0.5) * fret_w
                y = margin_y_top - 30
                self.create_text(x, y, text=label_text,
                                 fill=CONFIG["colors"]["text"],
                                 font=("Arial", 12, "bold"),
                                 anchor="s")

        self.x_hitboxes = []
        for s, f in (getattr(self.data, "x_positions", set()) or set()):
            if f == 0:
                cx = margin_x - 25
            else:
                cx = margin_x + (f - 0.5) * fret_w
            cy = margin_y_top + s * string_h
            hit_radius = 18
            self.x_hitboxes.append({'rect': (cx-hit_radius, cy-hit_radius, cx+hit_radius, cy+hit_radius), 'pos': (s, f)})

            if self.hovered_xpos == (s, f):
                self.create_rectangle(cx-hit_radius-4, cy-hit_radius-4, cx+hit_radius+4, cy+hit_radius+4,
                                       fill="", outline=CONFIG["colors"]["dot_hover"], width=2)

            self.create_text(cx, cy, text="X", fill=CONFIG["colors"]["dot_selected"], font=("Arial", 18, "bold"))

        barre_groups = get_barre_groups(self.data)
        preview_groups = get_preview_barre_groups(self.data, self.grid_hover)
        barre_lookup = self._barre_group_lookup(barre_groups)
        barre_positions = {pos for group in barre_groups for pos in group.notes}

        self.barre_hitboxes = []
        for group in barre_groups:
            selected = self.selected_barre_key == group.key
            hovered = self.hovered_barre_key == group.key
            outline_color = CONFIG["colors"]["dot_selected"] if selected else CONFIG["colors"]["dot_hover"] if hovered else "#ffffff"
            self._draw_barre(
                group,
                margin_x,
                margin_y_top,
                fret_w,
                string_h,
                fill_color=group.color,
                outline_color=outline_color,
                selected=selected,
                hovered=hovered,
                preview=False,
            )

        for group in preview_groups:
            if group.key in barre_lookup:
                continue
            self._draw_barre(
                group,
                margin_x,
                margin_y_top,
                fret_w,
                string_h,
                fill_color=group.color,
                outline_color=CONFIG["colors"]["dot_hover"],
                selected=False,
                hovered=False,
                preview=True,
            )

        self.hitboxes = []
        for s, f in self.data.positions:
            cy = margin_y_top + s * string_h

            if f == 0:
                cx = margin_x - 25
                hit_radius = 18
                self.hitboxes.append({'rect': (cx-hit_radius, cy-hit_radius, cx+hit_radius, cy+hit_radius), 'pos': (s, f)})

                key = f"{s},{f}"
                default_dot_color = getattr(self.data, "dot_color", CONFIG["colors"]["dot"]) or CONFIG["colors"]["dot"]
                dot_color = (getattr(self.data, "dot_colors", {}) or {}).get(key, default_dot_color) or default_dot_color
                is_small = getattr(self.data, "dot_small", {}).get(key, False)
                radius = CONFIG["dimensions"]["dot_small_radius"] if is_small else 11

                if self.hovered_pos == (s, f):
                    self.create_rectangle(cx-radius-4, cy-radius-4, cx+radius+4, cy+radius+4,
                                           fill="", outline=CONFIG["colors"]["dot_hover"], width=2)

                self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=dot_color, outline="#ffffff", width=2)

                label = (getattr(self.data, "dot_texts", {}) or {}).get(key, "")
                label = apply_symbol_map((label or "").strip()[:2])
                if label:
                    r, g, b = hex_to_rgb01(dot_color)
                    luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                    text_color = "#0f172a" if luminance > 0.62 else "#ffffff"
                    font_size = 9 if len(label) > 1 else 12
                    self.create_text(cx, cy, text=label, fill=text_color, font=("Arial", font_size, "bold"))
                continue

            if (s, f) in barre_positions:
                group = next((g for g in barre_groups if g.fret == f and s in g.strings), None)
                if group is not None:
                    geom = self._barre_geometry(group, margin_x, margin_y_top, fret_w, string_h)
                    cx = geom["cx"]
                    hit_radius = max(10, CONFIG["dimensions"]["dot_radius"] // 5 + 6)
                    self.hitboxes.append({
                        'rect': (cx-hit_radius, cy-hit_radius, cx+hit_radius, cy+hit_radius),
                        'pos': (s, f),
                        'barre_key': group.key,
                    })

                    if self.hovered_pos == (s, f):
                        self.create_rectangle(cx-hit_radius-3, cy-hit_radius-3, cx+hit_radius+3, cy+hit_radius+3,
                                               fill="", outline=CONFIG["colors"]["dot_hover"], width=2)

                    marker_radius = max(3, CONFIG["dimensions"]["dot_radius"] // 5)
                    self.create_oval(cx - marker_radius, cy - marker_radius, cx + marker_radius, cy + marker_radius,
                                     fill=group.color, outline="#ffffff", width=1)

                    label = (group.labels.get(s, "") or "").strip()[:2]
                    label = apply_symbol_map(label)
                    if label:
                        r, g, b = hex_to_rgb01(group.color)
                        luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                        text_color = "#0f172a" if luminance > 0.62 else "#ffffff"
                        font_size = 9 if len(label) > 1 else 11
                        self.create_text(cx, cy, text=label, fill=text_color, font=("Arial", font_size, "bold"))
                    continue

            cx = margin_x + (f - 0.5) * fret_w
            hit_radius = 20
            self.hitboxes.append({'rect': (cx-hit_radius, cy-hit_radius, cx+hit_radius, cy+hit_radius), 'pos': (s, f)})

            key = f"{s},{f}"
            default_dot_color = getattr(self.data, "dot_color", CONFIG["colors"]["dot"]) or CONFIG["colors"]["dot"]
            dot_color = (getattr(self.data, "dot_colors", {}) or {}).get(key, default_dot_color) or default_dot_color
            dot_type = getattr(self.data, "dot_types", {}).get(key, "circle")
            is_small = getattr(self.data, "dot_small", {}).get(key, False)

            if self.hovered_pos == (s, f):
                color = dot_color  # Use actual dot color
                radius = (CONFIG["dimensions"]["dot_small_radius"] if is_small else CONFIG["dimensions"]["dot_radius"]) + 3
            else:
                color = dot_color
                radius = CONFIG["dimensions"]["dot_small_radius"] if is_small else CONFIG["dimensions"]["dot_radius"]

            if self.hovered_pos == (s, f):
                self.create_rectangle(cx-radius-4, cy-radius-4, cx+radius+4, cy+radius+4,
                                       fill="", outline=CONFIG["colors"]["dot_hover"], width=2)

            if dot_type == "square":
                self.create_rectangle(cx - radius, cy - radius, cx + radius, cy + radius, fill=color, outline="")
                self.create_rectangle(cx - radius, cy - radius, cx + radius, cy + radius, outline="#ffffff", width=2)
            elif dot_type == "triangle":
                points = [cx, cy - radius, cx - radius, cy + radius, cx + radius, cy + radius]
                self.create_polygon(points, fill=color, outline="#ffffff", width=2)
            else:
                self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=color, outline="")
                self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#ffffff", width=2)

            label = (getattr(self.data, "dot_texts", {}) or {}).get(key, "")
            label = apply_symbol_map((label or "").strip()[:2])
            if label:
                r, g, b = hex_to_rgb01(color)
                luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                text_color = "#0f172a" if luminance > 0.62 else "#ffffff"
                font_size = 10 if len(label) > 1 else 13
                self.create_text(cx, cy, text=label, fill=text_color, font=("Arial", font_size, "bold"))

    def on_double_click(self, event):
        margin_x = CONFIG["dimensions"]["margin_side"]

        if event.y < CONFIG["dimensions"]["margin_top"] - 10:
            fret_w = (self.winfo_width() - 2 * margin_x) / self.data.num_frets
            fret_idx = int((event.x - margin_x) / fret_w) + 1

            if 0 < fret_idx <= self.data.num_frets:
                from constants import ask_text
                current_label = self.data.labels.get(str(fret_idx), "")
                new_label = ask_text(self.winfo_toplevel(), "Label Fret", f"Label for fret {fret_idx}:", current_label)

                if new_label is not None:
                    if new_label.strip():
                        self.data.labels[str(fret_idx)] = new_label.strip()
                    else:
                        self.data.labels.pop(str(fret_idx), None)
                    self.draw()
                    self.on_change()

    def on_right_click(self, event):
        margin_x = CONFIG["dimensions"]["margin_side"]
        margin_y_top = CONFIG["dimensions"]["margin_top"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))
        string_h = (self.winfo_height() - margin_y_top - CONFIG["dimensions"]["margin_bottom"]) / (string_count - 1)
        fret_w = (self.winfo_width() - 2 * margin_x) / self.data.num_frets

        clicked_dot = None
        for hb in self.hitboxes:
            x1, y1, x2, y2 = hb['rect']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                clicked_dot = hb['pos']
                break
        if clicked_dot:
            s, f = clicked_dot
            key = f"{s},{f}"
            current_label = (getattr(self.data, "dot_texts", {}) or {}).get(key, "")[:2]
            current_color = (getattr(self.data, "dot_colors", {}) or {}).get(key, "")
            default_color = getattr(self.data, "dot_color", CONFIG["colors"]["dot"]) or CONFIG["colors"]["dot"]

            from constants import ask_dot_properties
            res = ask_dot_properties(self.winfo_toplevel(), default_color, current_label, current_color)
            if res is not None:
                new_label, new_color = res

                if not hasattr(self.data, "dot_texts") or self.data.dot_texts is None:
                    self.data.dot_texts = {}
                if not hasattr(self.data, "dot_colors") or self.data.dot_colors is None:
                    self.data.dot_colors = {}

                new_label = (new_label or "").strip()[:2]
                if new_label:
                    self.data.dot_texts[key] = new_label
                else:
                    self.data.dot_texts.pop(key, None)

                new_color = (new_color or "").strip()
                if new_color:
                    self.data.dot_colors[key] = new_color
                else:
                    self.data.dot_colors.pop(key, None)

                self.draw()
                self.on_change()
            return

        clicked_x = None
        for hb in self.x_hitboxes:
            x1, y1, x2, y2 = hb['rect']
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                clicked_x = hb['pos']
                break
        if clicked_x:
            self.data.x_positions.discard(clicked_x)
            self.selected_barre_key = None
            self.draw()
            self.on_change()
            return

        s_idx = int((event.y - margin_y_top) / string_h)
        if not (0 <= s_idx < string_count):
            return

        if event.x <= margin_x - 10:
            f_idx = 0
        else:
            f_idx = int((event.x - margin_x) / fret_w) + 1
            if not (1 <= f_idx <= self.data.num_frets):
                return

        self.data.x_positions.add((s_idx, f_idx))
        self.data.positions.discard((s_idx, f_idx))
        if f_idx == 0:
            self.data.positions = set((s, f) for (s, f) in self.data.positions if s != s_idx)
            if hasattr(self.data, "dot_texts") and self.data.dot_texts:
                prefix = f"{s_idx},"
                for k in list(self.data.dot_texts.keys()):
                    if k.startswith(prefix):
                        self.data.dot_texts.pop(k, None)
            if hasattr(self.data, "dot_colors") and self.data.dot_colors:
                prefix = f"{s_idx},"
                for k in list(self.data.dot_colors.keys()):
                    if k.startswith(prefix):
                        self.data.dot_colors.pop(k, None)

        self.draw()
        self.on_change()

    def on_click(self, event):
        self.focus_set()
        barre_groups = get_barre_groups(self.data)
        clicked_barre = self._find_hitbox(self.barre_hitboxes, event.x, event.y)
        clicked_note = self._find_hitbox(self.hitboxes, event.x, event.y)
        clicked_group = None

        if clicked_barre:
            clicked_group = clicked_barre.get("group")
        elif clicked_note:
            clicked_group = self._is_note_part_of_barre(clicked_note["pos"], barre_groups)

        if clicked_group is not None:
            key = clicked_group.key
            if self.selected_barre_key == key and clicked_note and clicked_note["pos"] in clicked_group.notes:
                # Second click on a barre note removes just that note.
                s, f = clicked_note["pos"]
                self._remove_note_and_recompute_barre(s, f)
                self.draw()
                self.on_change()
                return

            # First click selects the whole barre.
            self.selected_barre_key = key
            self.draw()
            return

        if clicked_note:
            clicked_pos = clicked_note["pos"]
            self.data.positions.discard(clicked_pos)
            k = f"{clicked_pos[0]},{clicked_pos[1]}"
            if hasattr(self.data, "dot_texts") and self.data.dot_texts:
                self.data.dot_texts.pop(k, None)
            if hasattr(self.data, "dot_colors") and self.data.dot_colors:
                self.data.dot_colors.pop(k, None)
            if hasattr(self.data, "dot_types") and self.data.dot_types:
                self.data.dot_types.pop(k, None)
            if hasattr(self.data, "dot_small") and self.data.dot_small:
                self.data.dot_small.pop(k, None)
            if hasattr(self.data, "barre_excluded") and self.data.barre_excluded:
                self.data.barre_excluded.discard(clicked_pos)
            self.selected_barre_key = None
            self.draw()
            self.on_change()
            return

        margin_x = CONFIG["dimensions"]["margin_side"]
        margin_y_top = CONFIG["dimensions"]["margin_top"]
        string_count = max(2, int(getattr(self.data, "string_count", CONFIG["string_count"])))
        fret_w = (self.winfo_width() - 2 * margin_x) / self.data.num_frets
        string_h = (self.winfo_height() - margin_y_top - CONFIG["dimensions"]["margin_bottom"]) / (string_count - 1)

        s_idx = int((event.y - margin_y_top) / string_h)
        if 0 <= s_idx < string_count:
            if event.x <= margin_x - 10:
                f_idx = 0
            else:
                f_idx = int((event.x - margin_x) / fret_w) + 1
                if not (1 <= f_idx <= self.data.num_frets):
                    f_idx = None

            if f_idx is not None:
                self.data.positions.add((s_idx, f_idx))
                self.data.x_positions.discard((s_idx, f_idx))
                self.data.x_positions.discard((s_idx, 0))

                if not hasattr(self.data, "dot_colors") or self.data.dot_colors is None:
                    self.data.dot_colors = {}
                if not hasattr(self.data, "dot_types") or self.data.dot_types is None:
                    self.data.dot_types = {}
                if not hasattr(self.data, "dot_small") or self.data.dot_small is None:
                    self.data.dot_small = {}

                k = f"{s_idx},{f_idx}"
                self.data.dot_colors[k] = getattr(self.data, "dot_color", CONFIG["colors"]["dot"]) or CONFIG["colors"]["dot"]

                # Handle modifier keys
                dot_type = "circle"
                is_small = False

                if event.state & 0x0004:  # Ctrl key
                    dot_type = "square"
                if event.state & 0x0001:  # Shift key
                    dot_type = "triangle"
                if event.state & 0x20000:  # Alt key
                    is_small = True

                # Mix: if both ctrl and shift, prioritize square
                if event.state & 0x0004 and event.state & 0x0001:
                    dot_type = "square"

                self.data.dot_types[k] = dot_type
                if is_small:
                    self.data.dot_small[k] = True

        self.selected_barre_key = None
        self.draw()
        self.on_change()
