import json
import os
import random
from typing import Dict, List, Any

# ---------- File loading helpers ----------

def _resolve_spells_path() -> str:
    """
    Tries the project-relative data path first (../data/spells.json),
    then falls back to an absolute path override via env (SPELLS_JSON),
    and finally tries a local file next to this module.
    """
    here = os.path.dirname(__file__)
    candidates = [
        os.path.normpath(os.path.join(here, "../data/spells.json")),
        os.environ.get("SPELLS_JSON"),
        os.path.join(here, "spells.json"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError("Could not locate spells.json in expected paths.")

def _load_spells() -> List[Dict[str, Any]]:
    path = _resolve_spells_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Normalization helpers ----------

def _norm_level(level_val: Any) -> int:
    """
    Converts 'cantrip' -> 0, numeric strings -> int, otherwise 0 as safe fallback.
    """
    if isinstance(level_val, str):
        if level_val.strip().lower() == "cantrip":
            return 0
        try:
            return int(level_val.strip())
        except ValueError:
            return 0
    if isinstance(level_val, (int, float)):
        return int(level_val)
    return 0

def _spell_belongs_to_class(spell: Dict[str, Any], cls_lc: str) -> bool:
    """
    Determines whether a spell belongs to a given class (lowercase key),
    primarily via 'classes' field; falls back to 'tags' if needed.
    """
    classes = spell.get("classes") or []
    if any(isinstance(c, str) and c.lower() == cls_lc for c in classes):
        return True
    tags = spell.get("tags") or []
    if any(isinstance(t, str) and t.lower() == cls_lc for t in tags):
        return True
    return False

def _crm_string(spell: Dict[str, Any]) -> str:
    """
    Builds a Components/Ritual/Materials string from the spell record.
    Uses components.raw if present; appends '; ritual' if ritual is True.
    """
    comp = spell.get("components") or {}
    raw = comp.get("raw")
    if not isinstance(raw, str):
        # Fallback: construct from booleans/material text if needed
        parts = []
        if comp.get("verbal"): parts.append("V")
        if comp.get("somatic"): parts.append("S")
        if comp.get("material"):
            mats = comp.get("materials_needed")
            if isinstance(mats, list) and mats:
                parts.append("M (" + ", ".join(mats) + ")")
            else:
                parts.append("M")
        raw = ", ".join(parts) if parts else ""
    out = raw or ""
    if spell.get("ritual") is True:
        out = f"{out}; ritual" if out else "ritual"
    return out

def _clean_desc(text: Any) -> str:
    """
    Ensures description is a clean single-line string (newlines → spaces).
    """
    if not isinstance(text, str):
        return ""
    return " ".join(text.splitlines()).strip()

# ---------- Public API ----------

def fill_spellcasting_info(char_class: str, character_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Returns a dict with the seven requested newline-joined fields for the character's class.
    Does not mutate character_data; call character_data.update(...) with the result.
    """
    # Normalize class to lowercase for matching in spells.json
    cls_lc = (char_class or "").strip().lower()
    all_spells = _load_spells()

    # Filter spells for this class
    class_spells = [s for s in all_spells if _spell_belongs_to_class(s, cls_lc)]

    # If you want to limit quantity or choose randomly, you can do so here.
    # Current behavior: include all class spells, ordered by (level, name).
    class_spells.sort(key=lambda s: (_norm_level(s.get("level")), str(s.get("name") or "")))

    # Build parallel lists
    levels: List[str] = []
    names: List[str] = []
    times: List[str] = []
    ranges: List[str] = []
    crms: List[str] = []
    schools: List[str] = []
    descs: List[str] = []

    for s in class_spells:
        lvl = _norm_level(s.get("level"))
        levels.append(str(lvl))
        names.append(str(s.get("name") or "").strip())
        times.append(str(s.get("casting_time") or "").strip())
        ranges.append(str(s.get("range") or "").strip())
        crms.append(_crm_string(s))
        schools.append(str(s.get("school") or "").strip())
        descs.append(_clean_desc(s.get("description")))

    # Join with single newline characters
    return {
        "Spell_Levels": "\n\n".join(levels),
        "Spell_Names": "\n\n".join(names),
        "Spell_Times": "\n\n".join(times),
        "Spell_Ranges": "\n\n".join(ranges),
        "Spell_CRMs": "\n\n".join(crms),
        "Spell_School": "\n\n".join(schools),
        "Spell_Description": "\n\n".join(descs),
    }
