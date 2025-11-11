import json
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional
import re
import re
from typing import Any, Mapping, Dict, List, Tuple, DefaultDict
from collections import defaultdict
from django.conf import settings
import os, inspect


# ----------------
# HELPERS
# ---------------

_dice_re = re.compile(r"^\s*(\d+)\s*[dD]\s*(\d+)\s*$")

def _expected_from_dice(dice: str) -> float:
    m = _dice_re.match(dice or "")
    if not m: 
        return 0.0
    n, s = int(m.group(1)), int(m.group(2))
    return n * (s + 1) / 2.0  # average of 1..s is (s+1)/2

# --- level parsing (keeps your "cantrip" -> 0 behavior) ---
def _norm_level_to_int(v: Any) -> int:
    if isinstance(v, int):
        return v
    s = str(v).strip().lower()
    if s in ("cantrip", "cantrips", "0"):
        return 0
    m = re.match(r"^\s*(\d+)", s)
    return int(m.group(1)) if m else 0

# --- class normalization and progression tables ---
_FULL = { 1:1,2:1,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,11:6,12:6,13:7,14:7,15:8,16:8,17:9,18:9,19:9,20:9 }
_HALF  = { 1:0,2:1,3:1,4:2,5:2,6:2,7:2,8:3,9:3,10:3,11:3,12:4,13:4,14:4,15:4,16:5,17:5,18:5,19:5,20:5 }
_THIRD = { 1:0,2:0,3:1,4:1,5:1,6:2,7:2,8:2,9:2,10:2,11:2,12:3,13:3,14:3,15:3,16:3,17:3,18:4,19:4,20:4 }
_WARL  = { 1:1,2:1,3:2,4:2,5:3,6:3,7:4,8:4,9:5,10:5,11:5,12:5,13:5,14:5,15:5,16:5,17:5,18:5,19:5,20:5 }

def _normalize_class_name(raw: str) -> str:
    if not raw:
        return ""
    s = str(raw).strip().lower()
    primary = s.split("/", 1)[0].strip()
    if "(" in primary:
        primary = primary.split("(", 1)[0].strip()
    primary = re.sub(r"\s+\d+$", "", primary)
    if primary in {"eldritch knight", "fighter eldritch knight"}:
        return "fighter (eldritch knight)"
    if primary in {"arcane trickster", "rogue arcane trickster"}:
        return "rogue (arcane trickster)"
    return primary

def _max_spell_level_for(class_name: str, level: int) -> int:
    c = _normalize_class_name(class_name)
    lvl = max(1, min(20, int(level or 1)))
    full  = {"bard","cleric","druid","sorcerer","wizard"}
    half  = {"paladin","ranger","artificer"}
    third = {"fighter (eldritch knight)","rogue (arcane trickster)"}
    warl  = {"warlock"}
    if c in full:   table = _FULL
    elif c in half: table = _HALF
    elif c in third: table = _THIRD
    elif c in warl: table = _WARL
    else: return 0
    return table.get(lvl, 0)

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

def _load_spells_default() -> List[Dict[str, Any]]:
    # tries ../data/spells.json relative to this file
    base = os.path.dirname(__file__)
    path = os.path.normpath(os.path.join(base, "../data/spells.json"))
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _ability_mod_from(character_data: Mapping[str, Any], ability: str, default_score: int = 10) -> int:
    try:
        score = int(character_data.get(ability, default_score))
    except Exception:
        score = default_score
    return (score - 10) // 2

# --- Cantrips known (PHB baselines). If you disagree, override via character_data["SpellQuota"]["0"] ---
_CANT_KNOWN = {
    "bard":      lambda L: 2 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 2/3/4
    "cleric":    lambda L: 3 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 3/4/5
    "druid":     lambda L: 2 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 2/3/4 (PHB errata often 2→3; adjust if desired)
    "sorcerer":  lambda L: 4 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 4/5/6
    "warlock":   lambda L: 2 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 2/3/4
    "wizard":    lambda L: 3 + (1 if L >= 4 else 0) + (1 if L >= 10 else 0),            # 3/4/5
    "paladin":   lambda L: 0,
    "ranger":    lambda L: 0,
    "artificer": lambda L: 2 + (1 if L >= 10 else 0) + (1 if L >= 20 else 0),           # 2/3/4
}

# --- Spells known totals (PHB baselines for known-casters). Prepared casters handled separately. ---
_BARD_KNOWN     = {1:4,2:5,3:6,4:7,5:8,6:9,7:10,8:11,9:12,10:13,11:14,12:15,13:16,14:18,15:19,16:19,17:20,18:22,19:22,20:22}
_SORC_KNOWN     = {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,12:12,13:13,14:13,15:14,16:14,17:15,18:15,19:15,20:15}
_WARLOCK_KNOWN  = {1:2,2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:10,11:11,12:11,13:12,14:12,15:13,16:13,17:14,18:14,19:15,20:15}
_RANGER_KNOWN   = {1:0,2:2,3:3,4:4,5:4,6:4,7:5,8:5,9:5,10:6,11:6,12:6,13:7,14:7,15:7,16:8,17:8,18:8,19:9,20:10}

def _default_spell_quota(class_name: str, level: int, character_data: Mapping[str, Any]) -> Dict[int, int]:
    """
    Return desired counts PER SPELL LEVEL, e.g. {0: 4, 1: 4, 2: 3, 3: 2}.
    If character_data['SpellQuota'] exists, that overrides this.
    """
    c = _normalize_class_name(class_name)
    L = max(1, min(20, int(level or 1)))
    max_lvl = _max_spell_level_for(class_name, L)

    # Cantrips per class
    cantrips = _CANT_KNOWN.get(c, lambda _L: 0)(L)

    # Prepared casters: total prepared and we distribute across 1..max_lvl
    if c in {"cleric","druid","wizard"}:
        mod = _ability_mod_from(character_data, {"cleric":"Wisdom","druid":"Wisdom","wizard":"Intelligence"}[c])
        total = max(1, mod + L)
        quota = {0: cantrips}
        # Distribute prepared spells top-down
        remain = total
        for sl in range(max_lvl, 0, -1):
            take = min(remain, 2 if sl >= 3 else 3)  # heuristic: bias toward higher tiers, cap a bit
            quota[sl] = take
            remain -= take
            if remain <= 0:
                break
        # If any still remain (low levels / low max), put into level 1
        if remain > 0:
            quota[1] = quota.get(1, 0) + remain
        return quota

    if c == "paladin":
        mod = _ability_mod_from(character_data, "Charisma")
        total = max(1, mod + (L // 2))
        quota = {0: cantrips}
        remain = total
        for sl in range(max_lvl, 0, -1):
            take = min(remain, 2 if sl >= 2 else 3)
            quota[sl] = take
            remain -= take
            if remain <= 0:
                break
        if remain > 0:
            quota[1] = quota.get(1, 0) + remain
        return quota

    if c == "artificer":
        mod = _ability_mod_from(character_data, "Intelligence")
        total = max(1, mod + (L // 2))
        quota = {0: cantrips}
        remain = total
        for sl in range(max_lvl, 0, -1):
            take = min(remain, 2 if sl >= 2 else 3)
            quota[sl] = take
            remain -= take
            if remain <= 0:
                break
        if remain > 0:
            quota[1] = quota.get(1, 0) + remain
        return quota

    # Known-spell casters: total known; distribute across 1..max_lvl
    if c == "bard":
        known = _BARD_KNOWN.get(L, 0)
    elif c == "sorcerer":
        known = _SORC_KNOWN.get(L, 0)
    elif c == "warlock":
        known = _WARLOCK_KNOWN.get(L, 0)
    elif c == "ranger":
        known = _RANGER_KNOWN.get(L, 0)
    else:
        known = 0

    # Subtract cantrips; the rest are leveled spells
    leveled = max(0, known)
    quota = {0: cantrips}
    remain = leveled
    # Heuristic: prefer higher levels first, but ensure at least 1st-level gets something
    for sl in range(max_lvl, 0, -1):
        take = min(remain, 2 if sl >= 3 else 3)
        quota[sl] = take
        remain -= take
        if remain <= 0:
            break
    if remain > 0:
        quota[1] = quota.get(1, 0) + remain
    return quota


# -------- main API --------

# --- NEW: levelups loader + progression extractor ----------------------------

def _load_levelups() -> Dict[str, Any]:
    """
    Load ../data/levelups.json (preferred) or ./levelups.json.
    Returns a dict with keys: "fullTable", "paladinRangerTable".
    """
    file_path = os.path.join(settings.BASE_DIR, "chargenapp", "data", "levelups.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    raise FileNotFoundError("levelups.json not found next to script or in ../data/")

def _progression_from_levelups(class_name: str, level: int) -> Dict[str, Any]:
    data = _load_levelups()
    c = _normalize_class_name(class_name)
    L = max(1, min(20, int(level or 1)))

    # --- Sorcerer branch (uses sorcererTable) -------------------------------
    if c == "sorcerer":
        table = data.get("sorcererTable") or data.get("fullTable") or []
        row = next((r for r in table if int(r.get("level", -1)) == L), None)
        if not row:
            return {}
        # pull slots and normalize keys 1..9
        slots = row.get("spellSlots", {}) or {}
        spell_slots = {i: int(slots.get(str(i), 0)) for i in range(1, 10)}
        max_slot = max((lvl for lvl, n in spell_slots.items() if int(n) > 0), default=0)

        # prefer the sorcerer-specific fields; fall back to generic if absent
        cantrips_known = int(row.get("sorcererCantripsKnown", row.get("cantripsKnown", 0)) or 0)
        spells_known   = int(row.get("sorcererSpellsKnown",   row.get("spellsKnown",   0)) or 0)
        spell_points   = int(row.get("sorcererSpellPoints", 0) or 0)

        return {
            "cantripsKnown": cantrips_known,
            "spellsKnown": spells_known,
            "spellSlots": spell_slots,
            "maxSlotLevel": max_slot,
            "sorceryPoints": spell_points,   # <- NEW: passthrough
        }

    # --- Paladin/Ranger branch (as you already have) ------------------------
    if c in {"paladin", "ranger"}:
        table = data.get("paladinRangerTable", [])
        row = next((r for r in table if int(r.get("level", -1)) == L), None)
        if not row:
            return {}
        sc = row.get("spellcasting", {}) or {}
        slots = sc.get("spellSlots", {}) or {}
        spell_slots = {i: int(slots.get(str(i), 0)) for i in range(1, 10)}
        max_slot = max((lvl for lvl, n in spell_slots.items() if int(n) > 0), default=0)
        return {
            "cantripsKnown": 0,
            "spellsKnown": int(sc.get("spellsKnown", 0) or 0),
            "spellSlots": spell_slots,
            "maxSlotLevel": max_slot,
        }

    # --- Default: full casters (Bard/Cleric/Druid/Wizard/etc.) --------------
    table = data.get("fullTable", [])
    row = next((r for r in table if int(r.get("level", -1)) == L), None)
    if not row:
        return {}
    slots = row.get("spellSlots", {}) or {}
    spell_slots = {i: int(slots.get(str(i), 0)) for i in range(1, 10)}
    max_slot = max((lvl for lvl, n in spell_slots.items() if int(n) > 0), default=0)
    return {
        "cantripsKnown": int(row.get("cantripsKnown", 0) or 0),
        "spellsKnown": int(row.get("spellsKnown", 0) or 0),
        "spellSlots": spell_slots,
        "maxSlotLevel": max_slot,
    }

# --- UPDATED: main API wired to levelups.json --------------------------------

def fill_spellcasting_info(class_name: str, character_data: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    # Spellcasting stats
    spellcasting_ability = (
        "Charisma" if class_name in {"Sorcerer", "Warlock", "Bard", "Paladin"} else
        "Wisdom"   if class_name in {"Cleric", "Druid", "Ranger"} else
        "Intelligence"
    )
    prof_bonus = int(character_data.get("ProficiencyBonus", 2))
    ability_score = int(character_data.get(spellcasting_ability, 10))
    ability_mod = (ability_score - 10) // 2
    spell_save_dc = 8 + prof_bonus + ability_mod
    spell_attack_bonus = prof_bonus + ability_mod
    level = int(character_data.get("Level", 1) or 1)

    out["SpellSaveDC"] = spell_save_dc
    out["SpellAttackBonus"] = spell_attack_bonus
    out["SpellcastingAbility"] = spellcasting_ability
    out["SpellcastingClass"] = class_name

    # Load spells and build the class pool
    all_spells = _load_spells_default()
    want = _normalize_class_name(class_name)

    def class_matches(sp: Mapping[str, Any]) -> bool:
        raw = sp.get("classes", [])
        if isinstance(raw, str):
            classes = [c.strip().lower() for c in raw.split(",") if c.strip()]
        else:
            classes = [str(c).strip().lower() for c in (raw or [])]
        return want in classes

    # --- NEW: pull progression from levelups.json; fallback to old logic if missing
    try:
        prog = _progression_from_levelups(class_name, level)    
    except Exception:
        prog = {}

    if prog:
        cantrips_known = int(prog.get("cantripsKnown", 0))
        spells_known_total = int(prog.get("spellsKnown", 0))
        slots_map = prog.get("spellSlots", {}) or {}
        max_lvl_from_slots = int(prog.get("maxSlotLevel", 0))
        max_lvl = max_lvl_from_slots if max_lvl_from_slots > 0 else _max_spell_level_for(class_name, level)
        if _normalize_class_name(class_name) == "sorcerer":
            out["SorceryPoints"] = int(prog.get("sorceryPoints", 0))
    else:
        # fallback to original computation if levelups.json not found/incomplete
        cantrips_known = _CANT_KNOWN.get(want, lambda _L: 0)(level)
        spells_known_total = 0  # prepared casters/others handled by quota below
        max_lvl = _max_spell_level_for(class_name, level)
        slots_map = {i: (1 if i <= max_lvl else 0) for i in range(1, 10)}  # minimal placeholder

    # --- build class spell pool, capped by max level from levelups
    from collections import defaultdict
    pool_by_level: DefaultDict[int, List[Mapping[str, Any]]] = defaultdict(list)
    for sp in all_spells:
        if not class_matches(sp):
            continue
        sl = _norm_level_to_int(sp.get("level", 0))
        if sl > max_lvl:
            continue
        pool_by_level[sl].append(sp)

    for sl in pool_by_level:
        pool_by_level[sl].sort(key=lambda sp: (_norm_level_to_int(sp.get("level", 0)),
                                               str(sp.get("name", "")).lower()))

    # --- quotas (driven by levelups.json) ------------------------------------
    # Allow explicit override via character_data["SpellQuota"] (same as before)
    override = character_data.get("SpellQuota", {})
    if override:
        quota: Dict[int, int] = {int(k): int(v) for k, v in override.items()}
    else:
        quota = {0: cantrips_known}

        # For leveled spells:
        # If levelups gave us spellSlots, distribute known/prepared spells across
        # the slot levels that actually exist, top-down, ensuring 1+ at 1st if any remain.
        remaining = max(0, int(spells_known_total))
        levels_in_use = [lvl for lvl in range(1, 10) if int(slots_map.get(lvl, 0)) > 0 and lvl <= max_lvl]
        levels_in_use.sort(reverse=True)

        # First pass: give at most 2 to higher tiers and 3 to 1st/2nd (keeps variety)
        for sl in levels_in_use:
            if remaining <= 0:
                break
            cap = 2 if sl >= 3 else 3
            take = min(cap, remaining)
            quota[sl] = take
            remaining -= take

        # If spells remain (e.g., big known lists), dump into 1st
        if remaining > 0:
            quota[1] = quota.get(1, 0) + remaining

    # --- select spells per quota (unchanged behavior) ------------------------
    selected: List[Mapping[str, Any]] = []
    for sl in sorted(quota.keys(), reverse=True):
        if sl < 0:
            continue
        need = int(quota.get(sl, 0))
        if need <= 0:
            continue
        available = pool_by_level.get(sl, [])
        take = min(need, len(available))
        selected.extend(available[:take])

    # If short, roll remainder downwards
    total_quota = sum(max(0, v) for v in quota.values())
    if len(selected) < total_quota:
        missing = total_quota - len(selected)
        remaining_pool: List[Tuple[int, Mapping[str, Any]]] = []
        already = {id(s) for s in selected}
        for sl in sorted(pool_by_level.keys(), reverse=True):
            for sp in pool_by_level[sl]:
                if id(sp) not in already:
                    remaining_pool.append((sl, sp))
        for _, sp in remaining_pool[:missing]:
            selected.append(sp)

    # --- serialize into Spell1..Spell30 + flattened columns ------------------
    def _crm_from_components(components) -> str:
        if isinstance(components, str):
            return components
        if isinstance(components, list):
            return "".join(x for x in components if isinstance(x, str))[:3]
        if isinstance(components, dict):
            return "".join(k for k, v in components.items() if v)[:3]
        return ""

    def _row_from_spell(sp: Mapping[str, Any]) -> List[str]:
        lvl = str(_norm_level_to_int(sp.get("level", 0)))
        return [
            lvl,
            str(sp.get("name", "")),
            str(sp.get("casting_time", "")),
            str(sp.get("range", "")),
            _crm_from_components(sp.get("components")),
            str(sp.get("school", "")),
        ]

    top_spell_candidates = []
    
    for i in range(30):
        row = _row_from_spell(selected[i]) if i < len(selected) else ["", "", "", "", "", ""]
        out[f"Spell{i+1}"] = row
        lvl, name, ctime, rng, crm, school = ("" if v is None else str(v) for v in (row + [""] * 6)[:6])
        out[f"Spell{i+1}Level"]  = lvl
        out[f"Spell{i+1}Name"]   = name
        out[f"Spell{i+1}Time"]   = ctime
        out[f"Spell{i+1}Range"]  = rng
        out[f"Spell{i+1}CRM"]    = crm
        out[f"Spell{i+1}School"] = school
        top_spell_candidates.append({"name": name, "level": lvl, "damage_dice": ((selected[i] if i < len(selected) else {}) or {}).get("basic_damage") or ((selected[i] if i < len(selected) else {}) or {}).get("damage_dice") or ""})

    # ID top spell and cantrip

    top_spell_candidates = sorted(top_spell_candidates, key=lambda x: _expected_from_dice(x.get("damage_dice","")), reverse=True)
    top_spell_candidates = list(filter(None, [next((s for s in top_spell_candidates if int(s.get("level") or 0) == 0), None), next((s for s in top_spell_candidates if int(s.get("level") or 0) > 0), None)]))

    # Sort descending by expected damage; ties break on level (higher first)
    top_spell_candidates = sorted(
        top_spell_candidates,
        key=lambda x: (_expected_from_dice(x.get("damage_dice", "")), int(x.get("level") or 0)),
        reverse=True,
    )
    print(top_spell_candidates)
    character_data.update({"SpellCandidates": top_spell_candidates})
    
    return out
