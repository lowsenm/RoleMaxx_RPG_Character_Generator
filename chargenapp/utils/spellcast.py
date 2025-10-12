import json
import os
import re
from typing import Dict, List, Any

# ---------- File loading helpers ----------

def _resolve_spells_path() -> str:
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
    spells = _load_spells()
    return {s["name"]: s for s in spells if isinstance(s, dict) and "name" in s}

# ---------- Normalization helpers ----------

def _norm_level(level_val: Any) -> int:
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
    classes = spell.get("classes") or []
    if any(isinstance(c, str) and c.lower() == cls_lc for c in classes):
        return True
    tags = spell.get("tags") or []
    if any(isinstance(t, str) and t.lower() == cls_lc for t in tags):
        return True
    return False

def _crm_string(spell: Dict[str, Any]) -> str:
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
    if not isinstance(text, str):
        return ""
    return " ".join(text.splitlines()).strip()

# ---------- Ability / Proficiency helpers ----------

_CLASS_TO_ABILITY = {
    "artificer": "Intelligence",
    "bard": "Charisma",
    "cleric": "Wisdom",
    "druid": "Wisdom",
    "paladin": "Charisma",
    "ranger": "Wisdom",
    "sorcerer": "Charisma",
    "warlock": "Charisma",
    "wizard": "Intelligence",
}

def _canonical_class(char_class: str) -> str:
    cls = (char_class or "").strip()
    return cls[:1].upper() + cls[1:].lower()

def _spellcasting_ability_for_class(char_class: str) -> str:
    key = (char_class or "").strip().lower()
    return _CLASS_TO_ABILITY.get(key, "Intelligence")

def _parse_int_any(x: Any, default: int = 0) -> int:
    if isinstance(x, (int, float)): 
        return int(x)
    if isinstance(x, str):
        m = re.search(r"-?\d+", x)
        if m:
            try:
                return int(m.group(0))
            except ValueError:
                pass
    return default

def _ability_mod_from_score(score: int) -> int:
    return (int(score) - 10) // 2

def _get_ability_mod(character_data: Dict[str, Any], ability: str) -> int:
    # Try common modifier keys
    candidates = [
        f"{ability}Mod",
        f"{ability} Mod",
        f"{ability[:3].upper()}_mod",
        f"{ability[:3].upper()}_MOD",
        f"{ability[:3].upper()}Mod",
        f"{ability[:3].upper()} Mod",
    ]
    for k in candidates:
        if k in character_data:
            return _parse_int_any(character_data[k], 0)

    # Try to compute from score if present
    for key in [ability, ability.upper(), ability[:3].upper(), f"{ability} Score", f"{ability}Score"]:
        if key in character_data:
            return _ability_mod_from_score(_parse_int_any(character_data[key], 10))

    # Fallback
    return 0

def _get_proficiency_bonus(character_data: Dict[str, Any]) -> int:
    if "ProficiencyBonus" in character_data:
        return _parse_int_any(character_data["ProficiencyBonus"], 2)
    lvl = _parse_int_any(character_data.get("Level", 1), 1)
    if lvl <= 4: return 2
    if lvl <= 8: return 3
    if lvl <= 12: return 4
    if lvl <= 16: return 5
    return 6

def _format_bonus(n: int) -> str:
    return f"+{n}" if n >= 0 else str(n)

# ---------- Public API ----------

def fill_spellcasting_info(char_class: str, character_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Returns:
      - Seven newline-joined fields:
        Spell_Levels, Spell_Names, Spell_Times, Spell_Ranges, Spell_CRMs, Spell_School, Spell_Description
      - Plus: SpellcastingClass, SpellcastingAbility, SpellAttackBonus
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
        descs.append(_clean_desc(s.get("description") if "description" in s else s.get("desc")))

    # Compute casting ability & attack bonus
    casting_ability = _spellcasting_ability_for_class(char_class)
    ability_mod = _get_ability_mod(character_data, casting_ability)
    prof = _get_proficiency_bonus(character_data)
    spell_attack_bonus = ability_mod + prof

    return {
        "SpellcastingClass": _canonical_class(char_class),
        "SpellcastingAbility": casting_ability,
        "SpellAttackBonus": _format_bonus(spell_attack_bonus),
        "SpellLevels": "\n".join(levels),
        "SpellNames": "\n".join(names),
        "SpellTimes": "\n".join(times),
        "SpellRanges": "\n".join(ranges),
#        "SpellCRMs": "\n".join(crms),
        "SpellSchool": "\n".join(schools),
#        "SpellDescription": "\n".join(descs),
    }
