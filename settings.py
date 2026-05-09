import json
import os
import sys

DEFAULT_SETTINGS = {
    "dark_mode": True,
    "default_frets": 12,
    "default_string_count": 6,
    "dimensions": {
        "string_spacing": 55,
        "fret_spacing": 65,
        "margin_top": 80,
        "margin_bottom": 80,
        "margin_side": 60,
        "nut_width": 12,
        "dot_radius": 14,
        "dot_small_radius": 8,
        "marker_radius": 8
    },
    "preset_colors": [
        "#4cc9f0",
        "#ff6b6b",
        "#51cf66",
        "#ffd43b",
        "#cc5de8",
        "#ff922b",
        "#20c997",
        "#f06595",
        "#5c7cfa",
        "#e599f7",
    ]
}

class SettingsManager:
    @staticmethod
    def get_settings_filepath():
        if getattr(sys, 'frozen', False):
            return os.path.join(os.path.dirname(sys.executable), "settings.json")
        else:
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

    @staticmethod
    def load_settings():
        filepath = SettingsManager.get_settings_filepath()
        if not os.path.exists(filepath):
            return DEFAULT_SETTINGS.copy()

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            if "dimensions" in data:
                settings["dimensions"].update(data["dimensions"])
            if "preset_colors" in data:
                settings["preset_colors"] = data["preset_colors"]
            return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(settings):
        filepath = SettingsManager.get_settings_filepath()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    @staticmethod
    def apply_to_config():
        """Apply settings to the CONFIG in constants.py"""
        from constants import CONFIG, get_colors
        settings = SettingsManager.load_settings()

        CONFIG["default_frets"] = settings["default_frets"]
        CONFIG["string_count"] = settings["default_string_count"]

        if "dimensions" in settings:
            for key, value in settings["dimensions"].items():
                if key in CONFIG["dimensions"]:
                    CONFIG["dimensions"][key] = value

        import constants
        constants.PRESET_COLORS = settings["preset_colors"]

        if settings.get("dark_mode", True):
            from customtkinter import set_appearance_mode
            set_appearance_mode("Dark")
        else:
            from customtkinter import set_appearance_mode
            set_appearance_mode("Light")

        CONFIG["colors"] = get_colors()
