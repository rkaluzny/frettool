from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
import json
from uuid import uuid4
from constants import CONFIG

class FretboardData:
    def __init__(self, title: str = "New Chord", description: str = "", num_frets: int = None):
        self.id = datetime.now().timestamp()
        self.title = title
        self.description = description
        self.num_frets = num_frets if num_frets is not None else CONFIG["default_frets"]
        self.string_count: int = CONFIG["string_count"]
        self.positions: Set[Tuple[int, int]] = set()
        self.labels: Dict[str, str] = {}
        self.dot_color: str = CONFIG["colors"]["dot"]
        self.x_positions: Set[Tuple[int, int]] = set()
        self.dot_texts: Dict[str, str] = {}
        self.dot_colors: Dict[str, str] = {}
        self.dot_types: Dict[str, str] = {}  # "s,f" -> "circle", "square", "triangle"
        self.dot_small: Dict[str, bool] = {}  # "s,f" -> True if alt+click (smaller dot)
        self.barre_excluded: Set[Tuple[int, int]] = set()  # positions disconnected from barres
        self.barres_disabled: bool = not CONFIG.get("barres_enabled_default", True)  # global disable for barre rendering

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "num_frets": self.num_frets,
            "string_count": self.string_count,
            "positions": list(self.positions),
            "labels": self.labels,
            "dot_color": self.dot_color,
            "x_positions": list(self.x_positions),
            "dot_texts": self.dot_texts,
            "dot_colors": self.dot_colors,
            "dot_types": self.dot_types,
            "dot_small": self.dot_small,
            "barre_excluded": list(self.barre_excluded),
            "barres_disabled": self.barres_disabled,
        }

    @staticmethod
    def from_dict(data):
        fb = FretboardData(data["title"], data["description"], data["num_frets"])
        fb.id = data["id"]
        fb.string_count = int(data.get("string_count", 6))
        fb.positions = set(tuple(p) for p in data["positions"])
        fb.labels = data.get("labels", {})
        fb.dot_color = data.get("dot_color", "#4cc9f0")
        if "x_positions" in data:
            fb.x_positions = set(tuple(p) for p in data.get("x_positions", []))
        else:
            fb.x_positions = set((s, 0) for s in data.get("muted_strings", []))
        fb.dot_texts = data.get("dot_texts", {}) or {}
        fb.dot_colors = data.get("dot_colors", {}) or {}
        fb.dot_types = data.get("dot_types", {}) or {}
        # Migrate old dot_dark to dot_small if present
        if "dot_dark" in data:
            fb.dot_small = data.get("dot_dark", {}) or {}
        else:
            fb.dot_small = data.get("dot_small", {}) or {}
        fb.barre_excluded = set(tuple(p) for p in data.get("barre_excluded", []))
        fb.barres_disabled = bool(data.get("barres_disabled", False))
        return fb

class ProjectData:
    def __init__(self, name: str = "Untitled Project"):
        self.id = str(uuid4())
        self.name = name
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.fretboards: List[FretboardData] = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "fretboards": [fb.to_dict() for fb in self.fretboards]
        }

    @staticmethod
    def from_dict(data):
        proj = ProjectData(data["name"])
        proj.id = data.get("id", str(uuid4()))
        proj.created_at = data["created_at"]
        proj.fretboards = [FretboardData.from_dict(fb) for fb in data["fretboards"]]
        return proj
