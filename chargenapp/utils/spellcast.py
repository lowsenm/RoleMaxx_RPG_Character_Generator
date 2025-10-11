import json
import os
import random
from typing import Dict, List, Any

# ---------- File loading helpers ----------

def _resolve_spells_path() -> str:
    """
    Prefer ../data/spells.json relative to this file; support env override (SPELLS_JSON);
    finally try a local spells.json next to this module.
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

# ---------- Back-compat helper (expected by chargen.py) ----------

def get_spell_data() -> Dict[str, Dict[str, Any]]:
    """
    Backward-compatible API expected by chargen.py.
    Returns a dict mapping spell name -> spell record.
    """
    spells = _load_spells()
    return {s["name"]: s for s in spells if isinstance(s, dict) and "name" in s}

# ---------- Normalization helpers ----------

def _norm_level(level_val: Any) -> int:
    """'cantrip' -> 0, numeric strings -> int, else safe 0."""
    if isinstance(level_val, str):
        lv = level_val.strip().lower()
        if lv == "cantrip":
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
    True if the spell is available to the given class (lowercase key),
    checking 'classes' primarily and falling back to 'tags'.
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
    Build the Components/Ritual/Materials string.
    Prefer components.raw; otherwise synthesize from booleans/materials.
    Append '; ritual' if ritual == True.
    """
    comp = spell.get("components") or {}
    raw = comp.get("raw")
    if not isinstance(raw, str):
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
    """Return single-line description (newlines → spaces)."""
    if not isinstance(text, str):
        return ""
    return " ".join(text.splitlines()).strip()

# ---------- Public API ----------

def fill_spellcasting_info(char_class: str, character_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Returns seven newline-joined fields for the character's class:
    Spell_Levels, Spell_Names, Spell_Times, Spell_Ranges, Spell_CRMs, Spell_School, Spell_Description.
    Does not mutate character_data.
    """
    cls_lc = (char_class or "").strip().lower()
    all_spells = _load_spells()

    # Filter to this class and sort by (level, name)
    class_spells = [s for s in all_spells if _spell_belongs_to_class(s, cls_lc)]
    class_spells.sort(key=lambda s: (_norm_level(s.get("level")), str(s.get("name") or "")))

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
        # Your json might use "description" (common) or "desc" (older)
        descs.append(_clean_desc(s.get("description") if "description" in s else s.get("desc")))

    return {
        "Spell_Levels": "\n\n".join(levels),
        "Spell_Names": "\n\n".join(names),
        "Spell_Times": "\n\n".join(times),
        "Spell_Ranges": "\n\n".join(ranges),
        "Spell_CRMs": "\n\n".join(crms),
        "Spell_School": "\n\n".join(schools),
        "Spell_Description": "\n\n".join(descs),
    }
