# chargenapp/utils/spellcast.py
import json
import os
import re
from typing import Dict, List, Any
from itertools import cycle

# ==============================
# Data loading
# ==============================

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

# Back-compat API expected by chargen.py
def get_spell_data() -> Dict[str, Dict[str, Any]]:
    spells = _load_spells()
    return {s["name"]: s for s in spells if isinstance(s, dict) and "name" in s}


# ==============================
# Normalization & formatting
# ==============================

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
        parts: List[str] = []
        if comp.get("verbal"): parts.append("V")
        if comp.get("somatic"): parts.append("S")
        if comp.get("material"):
            mats = comp.get("materials_needed")
            if isinstance(mats, list) and mats:
                parts.append("M (" + ", ".join(mats) + ")")
            else:
                parts.append("M")
        raw = ", ".join(parts) if parts else ""
    out = (raw or "").strip()
    if spell.get("ritual") is True:
        out = f"{out}; ritual" if out else "ritual"
    return out

def _clean_desc(text: Any) -> str:
    """Return single-line description (newlines → spaces)."""
    if not isinstance(text, str):
        return ""
    return " ".join(text.splitlines()).strip()


# ==============================
# Ability / proficiency helpers
# ==============================

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


# ==============================
# Spell count / level helpers
# ==============================

_FULL_CASTER = {"bard", "cleric", "druid", "sorcerer", "wizard"}
_HALF_CASTER = {"paladin", "ranger", "artificer"}
_PACT_CASTER = {"warlock"}

def _full_caster_max_level(level:int) -> int:
    # 2014 PHB baseline
    table = [0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,9,9]
    return table[min(max(level,0),20)]

def _half_caster_max_level(level:int, cls:str) -> int:
    # Half-caster “caster level” ≈ ceil(level/2). Artificer gets 1st-level at 1.
    eff = (level + 1)//2
    if cls == "artificer":
        eff = max(1, eff)
    return _full_caster_max_level(eff)

def _pact_max_level(level:int) -> int:
    # Warlock slot level progression (Pact Magic)
    table = [0,1,1,2,2,3,3,4,4,5,5,5,5,5,5,5,5,5,5,5,5]
    return table[min(max(level,0),20)]

def _max_spell_level_for(cls_lc:str, level:int) -> int:
    if cls_lc in _FULL_CASTER: return _full_caster_max_level(level)
    if cls_lc in _HALF_CASTER: return _half_caster_max_level(level, cls_lc)
    if cls_lc in _PACT_CASTER: return _pact_max_level(level)
    return _full_caster_max_level(level)

def _cantrips_known(cls_lc:str, level:int) -> int:
    # 2014 PHB baselines (compact approximations)
    if cls_lc in {"cleric","druid"}:
        return 3 + (1 if level>=4 else 0) + (1 if level>=10 else 0)
    if cls_lc == "bard":
        return 2 + (1 if level>=4 else 0) + (1 if level>=10 else 0)
    if cls_lc == "wizard":
        return 3 + (1 if level>=4 else 0) + (1 if level>=10 else 0)
    if cls_lc == "sorcerer":
        return 4 + (1 if level>=4 else 0) + (1 if level>=10 else 0)
    if cls_lc == "warlock":
        return 2 + (1 if level>=4 else 0) + (1 if level>=10 else 0)
    if cls_lc == "artificer":
        return 2 + (1 if level>=10 else 0)  # 3 at 10+
    # Paladin/Ranger (2014) have no cantrips
    return 0

def _spells_known_for_known_casters(cls_lc:str, level:int) -> int:
    # Compact PHB-style approximations (leveled spells only)
    if cls_lc == "bard":
        table = [0,4,5,6,7,8,9,10,11,12,14,15,15,16,18,19,19,20,22,22,22]
        return table[min(max(level,0),20)]
    if cls_lc == "sorcerer":
        table = [0,2,3,4,5,6,7,8,9,10,11,12,12,13,13,14,14,15,15,15,15]
        return table[min(max(level,0),20)]
    if cls_lc == "warlock":
        table = [0,2,3,4,5,6,7,8,9,10,10,11,11,12,12,13,13,14,14,15,15]
        return table[min(max(level,0),20)]
    if cls_lc == "ranger":
        table = [0,0,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11]
        return table[min(max(level,0),20)]
    return 0

def _is_prepared_caster(cls_lc:str) -> bool:
    return cls_lc in {"cleric","druid","paladin","artificer","wizard"}

def _pick_cantrips(spells: List[Dict[str,Any]], want:int) -> List[Dict[str,Any]]:
    pool = [s for s in spells if _norm_level(s.get("level")) == 0]
    pool.sort(key=lambda s: str(s.get("name") or ""))
    return pool[:want] if want <= len(pool) else pool

def _pick_leveled_spells(spells: List[Dict[str,Any]], max_lvl:int, want_total:int) -> List[Dict[str,Any]]:
    """
    Balanced picker for prepared/known leveled spells:
    1) Ensure at least one spell from each level 1..max_lvl (high → low) if available.
    2) Fill remaining picks by cycling levels high → low to bias toward higher slots,
       keeping selection deterministic (sorted by name inside each level).
    """
    # bucket by level
    by_level: Dict[int, List[Dict[str,Any]]] = {lvl: [] for lvl in range(1, max_lvl+1)}
    for s in spells:
        lv = _norm_level(s.get("level"))
        if 1 <= lv <= max_lvl:
            by_level[lv].append(s)

    # sort each bucket by name for determinism
    for lv in by_level:
        by_level[lv].sort(key=lambda x: str(x.get("name") or ""))

    chosen: List[Dict[str,Any]] = []

    # Pass 1: guarantee at least one per level (top-down)
    for lv in range(max_lvl, 0, -1):
        bucket = by_level.get(lv, [])
        if bucket:
            chosen.append(bucket.pop(0))
            if len(chosen) >= want_total:
                return chosen

    # Pass 2: fill remaining, bias high levels by cycling high→low
    lv = max_lvl
    while len(chosen) < want_total and any(by_level.values()):
        bucket = by_level.get(lv, [])
        if bucket:
            chosen.append(bucket.pop(0))
        lv -= 1
        if lv == 0:
            lv = max_lvl

    return chosen

# ==============================
# Spell ordering
# ==============================
def _order_spells_level_asc(chosen: list) -> list:
    """Order by spell level 0..9, then by name."""
    return sorted(
        chosen,
        key=lambda s: (_norm_level(s.get("level")), str(s.get("name") or "")),
    )


# ==============================
# Public API
# ==============================

def fill_spellcasting_info(char_class: str, character_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Returns:
      - Seven newline-joined fields:
        Spell_Levels, Spell_Names, Spell_Times, Spell_Ranges, Spell_CRMs, Spell_School, Spell_Description
      - Plus: SpellcastingClass, SpellcastingAbility, SpellAttackBonus
    """
    all_spells = _load_spells()
    cls_lc = (char_class or "").strip().lower()
    level_int = _parse_int_any(character_data.get("Level", 1), 1)
    max_lvl = _max_spell_level_for(cls_lc, level_int)

    # Filter to this class
    class_spells = [s for s in all_spells if _spell_belongs_to_class(s, cls_lc)]
    class_spells.sort(key=lambda s: (_norm_level(s.get("level")), str(s.get("name") or "")))

    # --- choose spells to include on the sheet ---
    chosen: List[Dict[str, Any]] = []

    # Cantrips
    want_can = _cantrips_known(cls_lc, level_int)
    chosen += _pick_cantrips(class_spells, want_can)

    # Leveled spells (known or prepared)
    if _is_prepared_caster(cls_lc):
        ability = _spellcasting_ability_for_class(char_class)
        ability_mod = _get_ability_mod(character_data, ability)
        prepared = max(1, ability_mod + level_int)
        chosen += _pick_leveled_spells(class_spells, max_lvl, prepared)
    else:
        known = _spells_known_for_known_casters(cls_lc, level_int)
        # These tables are for leveled spells only; cantrips are separate.
        chosen += _pick_leveled_spells(class_spells, max_lvl, known)

    # --- build parallel lists from 'chosen' only ---

    chosen = _order_spells_level_asc(chosen)

    levels: List[str] = []
    names: List[str] = []
    times: List[str] = []
    ranges: List[str] = []
    crms: List[str] = []
    schools: List[str] = []
    descs: List[str] = []

    for s in chosen:
        lvl = _norm_level(s.get("level"))
        levels.append(str(lvl))
        names.append(str(s.get("name") or "").strip())
        times.append(str(s.get("casting_time") or "").strip())
        ranges.append(str(s.get("range") or "").strip())
        crms.append(_crm_string(s))
        schools.append(str(s.get("school") or "").strip())
        descs.append(_clean_desc(s.get("description") if "description" in s else s.get("desc")))

    # --- header fields (class/ability/attack bonus) ---
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
        "SpellCRMs": "\n".join(crms),
        "SpellSchool": "\n".join(schools),
        "SpellDescription": "\n".join(descs),
    }
