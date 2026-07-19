import i18n
from constants import CONFIG, FRET_MARKERS, hex_to_rgb01
from models import FretboardData, ProjectData
from tkinter import messagebox
from barre_utils import get_barre_groups

class ExportManager:
    @staticmethod
    def export_png_from_canvas(canvas_widget, filename: str):
        try:
            from PIL import Image
            import io
            ps_data = canvas_widget.postscript(colormode="color")
            img = Image.open(io.BytesIO(ps_data.encode("utf-8")))
            img.save(filename, "PNG")
            messagebox.showinfo(i18n.tr("dialogs.success"), i18n.tr("export.success_png"))
            return True
        except Exception as e:
            messagebox.showerror(i18n.tr("export.error"), str(e))
            return False

    @staticmethod
    def export_svg(project: ProjectData, filename: str):
        """Export all fretboards as separate SVG pages (prefixed by the filename)."""
        base = filename.rsplit(".", 1)[0]
        for i, fb in enumerate(project.fretboards):
            fb_filename = f"{base}_{i+1}.svg"
            ExportManager._export_svg_single(fb, fb_filename)
        messagebox.showinfo(i18n.tr("dialogs.success"), i18n.tr("export.success_svg_all"))

    @staticmethod
    def _export_svg_single(fretboard: FretboardData, filename: str):
        margin = CONFIG["dimensions"]["margin_side"]
        s_space = CONFIG["dimensions"]["string_spacing"]
        f_space = CONFIG["dimensions"]["fret_spacing"]
        string_count = max(2, int(getattr(fretboard, "string_count", CONFIG["string_count"])))

        width = margin * 2 + fretboard.num_frets * f_space
        height = CONFIG["dimensions"]["margin_top"] + CONFIG["dimensions"]["margin_bottom"] + (string_count - 1) * s_space

        bg_color = CONFIG["colors"]["bg"]
        svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="{bg_color}"/>
        '''

        string_color = CONFIG["colors"]["string"]
        for i in range(string_count):
            y = CONFIG["dimensions"]["margin_top"] + i * s_space
            stroke_w = 2 + (i * 0.6)
            svg_content += f'<line x1="{margin}" y1="{y}" x2="{width-margin}" y2="{y}" stroke="{string_color}" stroke-width="{stroke_w:.2f}" />'

        fret_color = CONFIG["colors"]["fret_line"]
        nut_color = CONFIG["colors"]["nut"]
        for i in range(fretboard.num_frets + 1):
            x = margin + i * f_space
            w = CONFIG["dimensions"]["nut_width"] if i == 0 else 2
            color = nut_color if i == 0 else fret_color
            svg_content += f'<line x1="{x}" y1="{CONFIG["dimensions"]["margin_top"]}" x2="{x}" y2="{height-CONFIG["dimensions"]["margin_bottom"]}" stroke="{color}" stroke-width="{w}" />'

        default_dot_color = fretboard.dot_color or CONFIG["colors"]["dot"]
        dot_colors = getattr(fretboard, "dot_colors", {}) or {}
        dot_types = getattr(fretboard, "dot_types", {}) or {}
        dot_small = getattr(fretboard, "dot_small", {}) or {}
        barre_groups = get_barre_groups(fretboard)
        barre_positions = {pos for group in barre_groups for pos in group.notes}

        def barre_geometry(group):
            cx = margin + (group.fret - 0.5) * f_space
            half_width = max(12, CONFIG["dimensions"]["barre_half_width"] + 4)
            top_string_y = CONFIG["dimensions"]["margin_top"] + group.start_string * s_space
            bottom_string_y = CONFIG["dimensions"]["margin_top"] + group.end_string * s_space
            top = top_string_y - half_width
            bottom = bottom_string_y + half_width
            return cx, half_width, top, bottom

        for s, f in sorted(getattr(fretboard, "x_positions", set()) or set()):
            if f == 0:
                x = margin - 25
            else:
                x = margin + (f - 0.5) * f_space
            y = CONFIG["dimensions"]["margin_top"] + s * s_space
            svg_content += f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-family="Arial" font-size="18" font-weight="bold" fill="#ff6b6b">X</text>'

        for group in barre_groups:
            cx, half_width, top, bottom = barre_geometry(group)
            fill = group.color
            outline = "#ffffff"
            body_height = max(half_width * 2, bottom - top)
            svg_content += f'<rect x="{cx - half_width}" y="{top}" width="{half_width * 2}" height="{body_height}" rx="{half_width}" ry="{half_width}" fill="{fill}" stroke="{outline}" stroke-width="2" />'

            marker_radius = max(3, CONFIG["dimensions"]["barre_marker_radius"])
            for string_idx in group.strings:
                cy = CONFIG["dimensions"]["margin_top"] + string_idx * s_space
                label = group.labels.get(string_idx, "")
                if not label:
                    svg_content += f'<circle cx="{cx}" cy="{cy}" r="{marker_radius}" fill="{fill}" stroke="#ffffff" stroke-width="1" />'
                if label:
                    from constants import apply_symbol_map
                    label = apply_symbol_map(label[:2])
                    r, g, b = hex_to_rgb01(fill)
                    luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                    text_fill = "#0f172a" if luminance > 0.62 else "#ffffff"
                    font_size = "9" if len(label) > 1 else "11"
                    svg_content += f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="Arial" font-size="{font_size}" font-weight="bold" fill="{text_fill}">{label}</text>'

        for s, f in fretboard.positions:
            if (s, f) in barre_positions and f > 0:
                continue
            key = f"{s},{f}"
            dot_color = dot_colors.get(key, default_dot_color) or default_dot_color
            is_small = dot_small.get(key, False)
            dot_type = dot_types.get(key, "circle")
            r_circle = CONFIG["dimensions"]["dot_small_radius"] if is_small else CONFIG["dimensions"]["dot_radius"]
            if f == 0:
                cx = margin - 25
            else:
                cx = margin + (f - 0.5) * f_space
            cy = CONFIG["dimensions"]["margin_top"] + s * s_space
            stroke_color = CONFIG["colors"]["text"] if CONFIG["colors"]["bg"] == "#1a1a2e" else "#0f172a"
            if dot_type == "square":
                svg_content += f'<rect x="{cx - r_circle}" y="{cy - r_circle}" width="{r_circle*2}" height="{r_circle*2}" fill="{dot_color}" stroke="{stroke_color}" stroke-width="2" />'
            elif dot_type == "triangle":
                points = f"{cx},{cy - r_circle} {cx - r_circle},{cy + r_circle} {cx + r_circle},{cy + r_circle}"
                svg_content += f'<polygon points="{points}" fill="{dot_color}" stroke="{stroke_color}" stroke-width="2" />'
            else:
                svg_content += f'<circle cx="{cx}" cy="{cy}" r="{r_circle}" fill="{dot_color}" stroke="{stroke_color}" stroke-width="2" />'

            label = (getattr(fretboard, "dot_texts", {}) or {}).get(key, "")
            if label:
                from constants import apply_symbol_map
                label = apply_symbol_map(label)
                r, g, b = hex_to_rgb01(dot_color)
                luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                text_fill = "#0f172a" if luminance > 0.62 else "#ffffff"
                font_size = "12" if len(label) > 1 else "16"
                svg_content += f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-family="Arial" font-size="{font_size}" font-weight="bold" fill="{text_fill}">{label}</text>'

        svg_content += "</svg>"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg_content)
        messagebox.showinfo(i18n.tr("dialogs.success"), i18n.tr("export.success_svg"))

    @staticmethod
    def _draw_fretboard_on_pdf(c, fb: FretboardData, x_offset, y_offset, fretboard_width, fretboard_height):
        from reportlab.lib.units import cm
        from constants import hex_to_rgb01

        string_count = max(2, int(getattr(fb, "string_count", CONFIG["string_count"])))
        pdf_string_spacing = fretboard_height / (string_count - 1)
        pdf_fret_spacing = fretboard_width / fb.num_frets

        c.setFillColorRGB(1.0, 1.0, 1.0)
        c.roundRect(x_offset, y_offset - fretboard_height, fretboard_width, fretboard_height, 0.2 * cm, fill=1, stroke=0)

        c.setStrokeColorRGB(0.25, 0.25, 0.25)
        for string_idx in range(string_count):
            string_y = y_offset - string_idx * pdf_string_spacing
            c.setLineWidth(0.04 * cm + (string_idx * 0.01 * cm))
            c.line(x_offset, string_y, x_offset + fretboard_width, string_y)

        for fret_idx in range(fb.num_frets + 1):
            fret_x = x_offset + fret_idx * pdf_fret_spacing
            line_width = CONFIG["dimensions"]["nut_width"] / 10 if fret_idx == 0 else 0.05 * cm
            color_rgb = (0.7, 0.6, 0.4) if fret_idx == 0 else (0.5, 0.5, 0.5)
            c.setStrokeColorRGB(*color_rgb)
            c.setLineWidth(line_width)
            c.line(fret_x, y_offset, fret_x, y_offset - fretboard_height)

        for fret_num, dot_count in FRET_MARKERS.items():
            if fret_num <= fb.num_frets:
                marker_x = x_offset + (fret_num - 0.5) * pdf_fret_spacing
                marker_radius = CONFIG["dimensions"]["marker_radius"] / 100 * cm
                c.setFillColorRGB(0.6, 0.6, 0.6)
                if dot_count == 1:
                    marker_y = y_offset - fretboard_height / 2
                    c.circle(marker_x, marker_y, marker_radius, fill=1)
                else:
                    marker_y1 = y_offset - fretboard_height * 0.3
                    marker_y2 = y_offset - fretboard_height * 0.7
                    c.circle(marker_x, marker_y1, marker_radius, fill=1)
                    c.circle(marker_x, marker_y2, marker_radius, fill=1)

        # Draw fret numbers (even frets) like in preview
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.setFont("Helvetica", 9)
        for fret_num in range(2, fb.num_frets + 1, 2):
            if fret_num <= fb.num_frets:
                num_x = x_offset + (fret_num - 0.5) * pdf_fret_spacing
                num_y = y_offset - fretboard_height - 0.8 * cm
                c.drawCentredString(num_x, num_y, str(fret_num))

        x_positions = getattr(fb, "x_positions", set()) or set()
        if x_positions:
            c.setFillColorRGB(0.95, 0.25, 0.25)
            c.setFont("Helvetica-Bold", 12)
            for s, f in x_positions:
                if f == 0:
                    pos_x = x_offset - 0.5 * cm
                else:
                    pos_x = x_offset + (f - 0.5) * pdf_fret_spacing
                pos_y = y_offset - s * pdf_string_spacing - 4
                c.drawCentredString(pos_x, pos_y, "X")

        barre_groups = get_barre_groups(fb)
        barre_positions = {pos for group in barre_groups for pos in group.notes}

        for group in barre_groups:
            pos_x = x_offset + (group.fret - 0.5) * pdf_fret_spacing
            half_width = CONFIG["dimensions"]["barre_half_width"] * 1.5 / 100 * cm
            top_y = y_offset - group.start_string * pdf_string_spacing
            bottom_y = y_offset - group.end_string * pdf_string_spacing
            rect_bottom = bottom_y - half_width
            rect_height = (top_y - bottom_y) + (half_width * 2)

            c.setFillColorRGB(*hex_to_rgb01(group.color))
            c.setStrokeColorRGB(1.0, 1.0, 1.0)
            c.setLineWidth(0.7)
            c.roundRect(pos_x - half_width, rect_bottom, half_width * 2, rect_height, half_width, fill=1, stroke=1)

            marker_radius = CONFIG["dimensions"]["barre_marker_radius"] * 1.5 / 100 * cm
            for string_idx in group.strings:
                pos_y = y_offset - string_idx * pdf_string_spacing
                label = group.labels.get(string_idx, "")
                if not label:
                    c.setFillColorRGB(*hex_to_rgb01(group.color))
                    c.setStrokeColorRGB(1.0, 1.0, 1.0)
                    c.circle(pos_x, pos_y, marker_radius, fill=1, stroke=1)
                if label:
                    from constants import apply_symbol_map
                    label = apply_symbol_map(label[:2])
                    r, g, b = hex_to_rgb01(group.color)
                    luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
                    text_rgb = (0.06, 0.06, 0.08) if luminance > 0.62 else (1.0, 1.0, 1.0)
                    c.setFillColorRGB(*text_rgb)
                    font_size = 7 if len(label) > 1 else 9
                    c.setFont("Helvetica-Bold", font_size)
                    c.drawCentredString(pos_x, pos_y - 2.5, label)

        dot_radius = CONFIG["dimensions"]["dot_radius"] * 1.5 / 100 * cm
        default_dot_color = getattr(fb, "dot_color", CONFIG["colors"]["dot"]) or CONFIG["colors"]["dot"]
        dot_colors = getattr(fb, "dot_colors", {}) or {}
        dot_texts = getattr(fb, "dot_texts", {}) or {}
        dot_types = getattr(fb, "dot_types", {}) or {}
        dot_small = getattr(fb, "dot_small", {}) or {}

        for s, f in fb.positions:
            if (s, f) in barre_positions and f > 0:
                continue
            if f == 0:
                pos_x = x_offset - 0.5 * cm
                r_circle = dot_radius * 0.75
            else:
                pos_x = x_offset + (f - 0.5) * pdf_fret_spacing
                r_circle = dot_radius
            pos_y = y_offset - s * pdf_string_spacing
            key = f"{s},{f}"
            dot_color = dot_colors.get(key, default_dot_color) or default_dot_color
            is_small = dot_small.get(key, False)
            if is_small:
                r_circle = CONFIG["dimensions"]["dot_small_radius"] * 1.5 / 100 * cm
            dot_type = dot_types.get(key, "circle")

            dot_rgb = hex_to_rgb01(dot_color)
            luminance = (0.2126 * dot_rgb[0]) + (0.7152 * dot_rgb[1]) + (0.0722 * dot_rgb[2])
            text_rgb = (0.06, 0.06, 0.08) if luminance > 0.62 else (1.0, 1.0, 1.0)

            c.setFillColorRGB(*dot_rgb)
            c.setStrokeColorRGB(0.06, 0.06, 0.08)
            c.setLineWidth(0.04 * cm)

            if dot_type == "square":
                c.rect(pos_x - r_circle, pos_y - r_circle, r_circle*2, r_circle*2, fill=1, stroke=1)
            elif dot_type == "triangle":
                path = c.beginPath()
                path.moveTo(pos_x, pos_y + r_circle)
                path.lineTo(pos_x - r_circle, pos_y - r_circle)
                path.lineTo(pos_x + r_circle, pos_y - r_circle)
                path.close()
                c.drawPath(path, fill=1, stroke=1)
            else:
                c.circle(pos_x, pos_y, r_circle, fill=1, stroke=1)

            label = (dot_texts.get(key, "") or "")
            if label:
                from constants import reverse_symbol_map
                label = reverse_symbol_map(label)
                c.setFillColorRGB(*text_rgb)
                font_size = 8 if len(label) > 1 else 10
                c.setFont("Helvetica-Bold", font_size)
                c.drawCentredString(pos_x, pos_y - 3, label)

        c.setFillColorRGB(0.1, 0.1, 0.2)
        c.setFont("Helvetica-Bold", 9)
        for fret_num_str, label_text in fb.labels.items():
            try:
                fret_num = int(fret_num_str)
                if 0 < fret_num <= fb.num_frets:
                    from constants import reverse_symbol_map
                    label_text = reverse_symbol_map(label_text)
                    label_x = x_offset + (fret_num - 0.5) * pdf_fret_spacing
                    label_y = y_offset + 0.15 * cm
                    text_width = c.stringWidth(label_text, "Helvetica-Bold", 10)
                    c.drawString(label_x - text_width/2, label_y, label_text)
            except ValueError:
                pass

    @staticmethod
    def export_pdf(project: ProjectData, filename: str):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.units import cm
            from reportlab.lib import colors

            c = pdf_canvas.Canvas(filename, pagesize=A4)
            width, height = A4

            margin = 1.2 * cm
            header_h = 1.35 * cm
            footer_h = 0.8 * cm
            card_gap = 0.30 * cm
            card_h = 6.0 * cm

            def draw_page_header(page_num: int):
                header_bg = "#fef9ee"
                header_line = CONFIG["colors"]["fret_line"]
                text_color = "#1e293b"
                text_muted = "#64748b"
                c.setFillColor(colors.HexColor(header_bg))
                c.rect(0, height - header_h, width, header_h, fill=1, stroke=0)
                c.setStrokeColor(colors.HexColor(header_line))
                c.setLineWidth(0.8)
                c.line(0, height - header_h, width, height - header_h)
                c.setFillColor(colors.HexColor(text_color))
                c.setFont("Helvetica-Bold", 14)
                c.drawString(margin, height - 0.95 * cm, project.name)
                c.setFont("Helvetica", 8.5)
                c.setFillColor(colors.HexColor(text_muted))
                exported_at = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M")
                c.drawRightString(width - margin, height - 0.95 * cm, i18n.tr("export.pdf_header", datetime=exported_at, page=page_num))

            def draw_page_footer():
                c.setFillColor(colors.HexColor("#94a3b8"))
                c.setFont("Helvetica", 7.5)
                c.drawString(margin, 0.45 * cm, i18n.tr("export.pdf_footer", app_name=CONFIG["app_name"]))

            def paint_page_background():
                bg = "#ffffff" if CONFIG["colors"]["bg"] == "#f8fafc" else "#ffffff"
                c.setFillColor(colors.HexColor(bg))
                c.rect(0, 0, width, height, fill=1, stroke=0)

            page_num = 1
            paint_page_background()
            draw_page_header(page_num)
            draw_page_footer()

            y_top = height - header_h - margin
            for fb in project.fretboards:
                if y_top - card_h < footer_h + margin:
                    c.showPage()
                    page_num += 1
                    paint_page_background()
                    draw_page_header(page_num)
                    draw_page_footer()
                    y_top = height - header_h - margin

                x0 = margin
                y0 = y_top - card_h
                card_w = width - 2 * margin

                c.setFillColor(colors.white)
                c.setStrokeColor(colors.HexColor("#e2e8f0"))
                c.setLineWidth(1)
                c.roundRect(x0, y0, card_w, card_h, 0.28 * cm, fill=1, stroke=1)

                c.setFillColor(colors.HexColor("#0f172a"))
                c.setFont("Helvetica-Bold", 12.5)
                title_text = fb.title or i18n.tr("export.pdf_default_title")
                title_max_width = card_w - 1.10 * cm
                title_available = title_text
                while c.stringWidth(title_available, "Helvetica-Bold", 12.5) > title_max_width and len(title_available) > 3:
                    title_available = title_available[:-1]
                if title_available != title_text:
                    title_available = title_available[:-3] + "..."
                c.drawString(x0 + 0.55 * cm, y0 + card_h - 0.70 * cm, title_available)

                c.setFillColor(colors.HexColor("#475569"))
                c.setFont("Helvetica", 8.5)
                if fb.description:
                    from constants import reverse_symbol_map
                    desc_text = reverse_symbol_map(fb.description)
                    desc_max_width = card_w - 1.10 * cm
                    desc_available = desc_text
                    while c.stringWidth(desc_available, "Helvetica", 8.5) > desc_max_width and len(desc_available) > 3:
                        desc_available = desc_available[:-1]
                    if desc_available != desc_text:
                        desc_available = desc_available[:-3] + "..."
                    c.drawString(x0 + 0.55 * cm, y0 + card_h - 1.15 * cm, desc_available)

                fret_x = x0 + 0.55 * cm
                fret_y_top = y0 + card_h - 1.45 * cm
                fret_w = card_w - 1.10 * cm
                fret_h = 3.35 * cm
                ExportManager._draw_fretboard_on_pdf(c, fb, fret_x, fret_y_top, fret_w, fret_h)

                y_top = y0 - card_gap

            c.save()
            messagebox.showinfo(i18n.tr("dialogs.success"), i18n.tr("export.success_pdf"))
        except ImportError:
            messagebox.showwarning(i18n.tr("export.library_missing_title"), i18n.tr("export.library_missing_message"))
        except Exception as e:
            messagebox.showerror(i18n.tr("export.error"), str(e))
