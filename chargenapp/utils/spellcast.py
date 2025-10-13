import json
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional

# -------- helpers --------

def _norm_level_to_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    s = str(v).strip().lower()
    if s in ("cantrip", "0"): return 0
    try:
        return int(s)
    except (TypeError, ValueError):
        return 0

def _crm_from_components(comp: Optional[Mapping[str, Any]]) -> str:
    if not comp:
        return ""
    raw = comp.get("raw")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    parts = []
    if comp.get("verbal"): parts.append("V")
    if comp.get("somatic"): parts.append("S")
    if comp.get("material"):
        mats = comp.get("materials_needed")
        if isinstance(mats, list) and mats:
            parts.append(f"M ({', '.join(map(str, mats))})")
        else:
            parts.append("M")
    return ", ".join(parts)

def _row_from_spell(sp: Mapping[str, Any]) -> List[str]:
    # normalize "cantrip" → 0 for the level column
    lvl = str(_norm_level_to_int(sp.get("level", 0)))
    return [
        lvl,                                   # level (0 for cantrips)
        str(sp.get("name", "")),
        str(sp.get("casting_time", "")),
        str(sp.get("range", "")),
        _crm_from_components(sp.get("components")),
        str(sp.get("school", "")),
    ]

# Max spell level unlocked by class & character level (5e SRD-style)
_FULL = [0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,9]         # bard/cleric/druid/sorcerer/wizard
_HALF = [0,0,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5]         # paladin/ranger
_THIRD= [0,0,0,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4,4]         # EK/Arcane Trickster
_WARL = [0,1,1,2,2,3,3,4,4,5,5,5,5,5,5,5,5,5,5,5]         # warlock (pact slot level)
_ARTI = [0,1,1,2,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5]         # artificer

def _max_spell_level_for(class_name: str, level: int) -> int:
    c = class_name.strip().lower()
    level = max(1, min(20, int(level or 1)))

    full = {"bard","cleric","druid","sorcerer","wizard"}
    half = {"paladin","ranger"}
    third = {"fighter (eldritch knight)","rogue (arcane trickster)","eldritch knight","arcane trickster"}
    warl = {"warlock"}
    arti = {"artificer"}

    if c in full:  table = _FULL
    elif c in half: table = _HALF
    elif c in third: table = _THIRD
    elif c in warl: table = _WARL
    elif c in arti: table = _ARTI
    else:
        # default to non-caster
        return 0
    return table[level]

def _load_spells_default() -> List[Dict[str, Any]]:
    # tries ../data/spells.json relative to this file
    base = os.path.dirname(__file__)
    path = os.path.normpath(os.path.join(base, "../data/spells.json"))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------- main API --------

def fill_spellcasting_info(class_name: str, character_data: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Build Spell1..Spell30 lists AND fan them out into SpellNLevel/Name/Time/Range/CRM/School
    so the PDF (positions.json) can print each column.

    Returns a dict you can .update(character_data) with directly.
    """
    # ---- existing selection logic (unchanged) ----
    level = int(character_data.get("Level", 1) or 1)
    max_lvl = _max_spell_level_for(class_name, level)

    # You likely already have a function or dataset that provides all candidate spells
    # in dict form like: {"name": "...", "level": 0..9, "casting_time": "...", "range": "...",
    #                     "components": "...", "school": "...", "classes": ["bard", ...]}
    # We'll assume you already have: `all_spells = _load_spells()` and `_row_from_spell(sp)`
    all_spells = _load_spells_default()

    def class_matches(sp: Mapping[str, Any]) -> bool:
        cls = sp.get("classes", [])
        # tolerate comma-separated strings or lists
        if isinstance(cls, str):
            classes = [c.strip().lower() for c in cls.split(",") if c.strip()]
        else:
            classes = [str(c).strip().lower() for c in (cls or [])]
        return class_name.strip().lower() in classes

    eligible = [
        sp for sp in all_spells
        if class_matches(sp) and _norm_level_to_int(sp.get("level", 0)) <= max_lvl
    ]

    # Sort by numeric level then name for predictable placement
    eligible.sort(key=lambda sp: (_norm_level_to_int(sp.get("level", 0)),
                                  str(sp.get("name", "")).lower()))

    # ---- build Spell1..Spell30 lists (unchanged behavior) ----
    out: Dict[str, Any] = {}
    for i in range(30):
        if i < len(eligible):
            out[f"Spell{i+1}"] = _row_from_spell(eligible[i])
        else:
            out[f"Spell{i+1}"] = ["", "", "", "", "", ""]  # [lvl, name, time, range, CRM, school]

    # ---- NEW: flatten for PDF ----
    # positions.json looks for SpellNLevel/Name/Time/Range/CRM/School
    for i in range(1, 31):
        row = out.get(f"Spell{i}", ["", "", "", "", "", ""])
        # pad/truncate and stringify defensively
        row = (list(row) + ["", "", "", "", "", ""])[:6]
        lvl, name, ctime, rng, crm, school = ("" if v is None else str(v) for v in row)

        out[f"Spell{i}Level"]  = lvl
        out[f"Spell{i}Name"]   = name
        out[f"Spell{i}Time"]   = ctime
        out[f"Spell{i}Range"]  = rng
        out[f"Spell{i}CRM"]    = crm
        out[f"Spell{i}School"] = school

    return out
