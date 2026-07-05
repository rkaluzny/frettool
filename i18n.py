import json
import locale
import os
import sys

LANGUAGES = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("pl", "Polski"),
    ("ru", "Русский"),
    ("es", "Español"),
    ("fr", "Français"),
    ("zh", "中文"),
    ("ja", "日本語"),
    ("he", "עברית"),
    ("ar", "العربية"),
]

LANGUAGE_CODES = [code for code, _ in LANGUAGES]
LANGUAGE_NAMES = {code: name for code, name in LANGUAGES}

_current_language = "en"
_translations = {}
_fallback = {}


def _locales_dir():
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, "locales"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales"))
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), "locales"))
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0]


def _load_translations(lang):
    filepath = os.path.join(_locales_dir(), f"{lang}.json")
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return {}


def detect_system_language():
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(128)
            if ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 128):
                lang = buf.value.split("-")[0].lower()
                if lang in LANGUAGE_CODES:
                    return lang
        except:
            pass
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            lang_map = {
                0x0409: "en", 0x0407: "de", 0x0415: "pl", 0x0419: "ru",
                0x040A: "es", 0x040C: "fr", 0x0804: "zh", 0x0411: "ja",
                0x040D: "he", 0x0401: "ar",
            }
            if lang_id in lang_map:
                return lang_map[lang_id]
        except:
            pass

    try:
        for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            val = os.environ.get(var, "")
            if val and "_" in val:
                lang = val.split("_")[0]
                if lang in LANGUAGE_CODES:
                    return lang
    except:
        pass

    try:
        loc = locale.getlocale(locale.LC_CTYPE)
        if loc and loc[0]:
            code = loc[0].split("_")[0].lower()
            if code in LANGUAGE_CODES:
                return code
    except:
        pass

    return "en"


def set_language(lang):
    global _current_language, _translations
    if lang is None or lang not in LANGUAGE_CODES:
        lang = detect_system_language()
    _current_language = lang
    _translations = _load_translations(lang)


def get_language():
    return _current_language


def tr(key, **kwargs):
    text = _translations.get(key)
    if text is None:
        text = _fallback.get(key)
    if text is None:
        return key
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text


_fallback = _load_translations("en")
set_language("en")
