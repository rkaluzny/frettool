from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class BarreGroup:
    fret: int
    strings: Tuple[int, ...]
    color: str
    notes: Tuple[Tuple[int, int], ...]
    labels: Dict[int, str]

    @property
    def start_string(self) -> int:
        return self.strings[0]

    @property
    def end_string(self) -> int:
        return self.strings[-1]

    @property
    def key(self) -> str:
        return f"{self.fret}:{self.start_string}-{self.end_string}"


def _note_key(string_idx: int, fret_idx: int) -> str:
    return f"{string_idx},{fret_idx}"


def _note_meta(fb, string_idx: int, fret_idx: int) -> Dict[str, object]:
    key = _note_key(string_idx, fret_idx)
    dot_types = getattr(fb, "dot_types", {}) or {}
    dot_small = getattr(fb, "dot_small", {}) or {}
    dot_colors = getattr(fb, "dot_colors", {}) or {}
    dot_texts = getattr(fb, "dot_texts", {}) or {}
    default_color = getattr(fb, "dot_color", None) or "#4cc9f0"

    return {
        "key": key,
        "type": dot_types.get(key, "circle"),
        "is_small": bool(dot_small.get(key, False)),
        "color": dot_colors.get(key, default_color) or default_color,
        "label": (dot_texts.get(key, "") or ""),
    }


def _is_visually_standard(fb, string_idx: int, fret_idx: int) -> bool:
    if fret_idx <= 0:
        return False
    positions = getattr(fb, "positions", set()) or set()
    if (string_idx, fret_idx) not in positions:
        return False
    meta = _note_meta(fb, string_idx, fret_idx)
    return meta["type"] == "circle" and not meta["is_small"]


def _fret_has_mixed_notes(fb, fret_idx: int) -> bool:
    positions = getattr(fb, "positions", set()) or set()
    for string_idx, pos_fret in positions:
        if pos_fret != fret_idx:
            continue
        if not _is_visually_standard(fb, string_idx, pos_fret):
            return True
    return False


def _contiguous_runs(strings: Sequence[int]) -> List[Tuple[int, ...]]:
    if not strings:
        return []

    runs: List[List[int]] = [[strings[0]]]
    for string_idx in strings[1:]:
        if string_idx == runs[-1][-1] + 1:
            runs[-1].append(string_idx)
        else:
            runs.append([string_idx])
    return [tuple(run) for run in runs if len(run) >= 2]


def _make_group(fb, fret_idx, string_run):
    notes = tuple((string_idx, fret_idx) for string_idx in string_run)
    first_meta = _note_meta(fb, string_run[0], fret_idx)
    labels = {}
    for string_idx in string_run:
        label = _note_meta(fb, string_idx, fret_idx)["label"].strip()[:2]
        if label:
            labels[string_idx] = label
    return BarreGroup(
        fret=fret_idx,
        strings=string_run,
        color=str(first_meta["color"]),
        notes=notes,
        labels=labels,
    )


def build_barre_groups_for_fret(fb, fret_idx: int, extra_standard_string: Optional[int] = None) -> List[BarreGroup]:
    if fret_idx <= 0:
        return []

    if getattr(fb, "barres_disabled", False):
        return []

    if _fret_has_mixed_notes(fb, fret_idx):
        return []

    positions = getattr(fb, "positions", set()) or set()

    all_strings = sorted(
        string_idx
        for string_idx, pos_fret in positions
        if pos_fret == fret_idx
    )

    if extra_standard_string is not None and extra_standard_string not in all_strings:
        all_strings = sorted(all_strings + [extra_standard_string])

    if len(all_strings) < 2:
        return []

    breaks = getattr(fb, "barre_excluded", set()) or set()

    groups: List[BarreGroup] = []
    for run in _contiguous_runs(all_strings):
        segments = []
        current = [run[0]]
        for i in range(1, len(run)):
            prev_s = run[i - 1]
            curr_s = run[i]
            if (prev_s, fret_idx) in breaks:
                segments.append(current)
                current = [curr_s]
            else:
                current.append(curr_s)
        segments.append(current)

        for segment in segments:
            eligible = [
                s for s in segment
                if _is_visually_standard(fb, s, fret_idx)
                   or (extra_standard_string is not None and s == extra_standard_string)
            ]
            if len(eligible) >= 2:
                groups.append(_make_group(fb, fret_idx, tuple(eligible)))

    return groups


def get_barre_groups(fb) -> List[BarreGroup]:
    frets = sorted({fret_idx for _, fret_idx in (getattr(fb, "positions", set()) or set()) if fret_idx > 0})
    groups: List[BarreGroup] = []
    for fret_idx in frets:
        groups.extend(build_barre_groups_for_fret(fb, fret_idx))
    return groups


def get_preview_barre_groups(fb, hovered_pos: Optional[Tuple[int, int]]) -> List[BarreGroup]:
    if not hovered_pos:
        return []

    string_idx, fret_idx = hovered_pos
    if fret_idx <= 0:
        return []

    positions = getattr(fb, "positions", set()) or set()
    if (string_idx, fret_idx) in positions:
        return []

    if _fret_has_mixed_notes(fb, fret_idx):
        return []

    return build_barre_groups_for_fret(fb, fret_idx, extra_standard_string=string_idx)
