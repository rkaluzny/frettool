import json
import os
import sys
from persistence import get_data_dir

DEFAULT_SETTINGS = {
    "language": None,
    "dark_mode": True,
    "default_frets": 12,
    "default_string_count": 6,
    "barres_enabled_default": True,
    "barre_min_strings": 2,
    "dimensions": {
        "string_spacing": 55,
        "fret_spacing": 65,
        "margin_top": 80,
        "margin_bottom": 80,
        "margin_side": 60,
        "nut_width": 12,
        "dot_radius": 14,
        "dot_small_radius": 8,
        "marker_radius": 8,
        "barre_half_width": 14,
        "barre_outline_width": 2,
        "barre_marker_radius": 3
    },
    "preset_colors": [
        "#ff6b6b",
        "#ffd43b",
        "#cc5de8",
        "#20c997",
    ]
}

class SettingsManager:
    @staticmethod
    def get_settings_filepath():
        from persistence import _migrate_file
        _migrate_file("settings.json")
        return os.path.join(get_data_dir(), "settings.json")

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
        import i18n
        from constants import CONFIG, get_colors
        settings = SettingsManager.load_settings()
        i18n.set_language(settings.get("language"))

        CONFIG["default_frets"] = settings["default_frets"]
        CONFIG["string_count"] = settings["default_string_count"]
        CONFIG["barres_enabled_default"] = settings.get("barres_enabled_default", True)
        CONFIG["barre_min_strings"] = settings.get("barre_min_strings", 2)

        if "dimensions" in settings:
            for key, value in settings["dimensions"].items():
                if key in CONFIG["dimensions"]:
                    CONFIG["dimensions"][key] = value

        import constants
        constants.PRESET_COLORS = settings["preset_colors"][:4]

        if settings.get("dark_mode", True):
            from customtkinter import set_appearance_mode
            set_appearance_mode("Dark")
        else:
            from customtkinter import set_appearance_mode
            set_appearance_mode("Light")

        CONFIG["colors"] = get_colors()
