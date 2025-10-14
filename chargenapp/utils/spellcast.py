import json
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional
import re
import re
from typing import Any, Mapping, Dict, List, Tuple, DefaultDict
from collections import defaultdict

# ----------------
# HELPERS
# ----------------

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

def fill_spellcasting_info(class_name: str, character_data: Mapping[str, Any]) -> Dict[str, Any]:
    level = int(character_data.get("Level", 1) or 1)
    max_lvl = _max_spell_level_for(class_name, level)

    all_spells = _load_spells_default()  # your existing loader
    want = _normalize_class_name(class_name)

    def class_matches(sp: Mapping[str, Any]) -> bool:
        raw = sp.get("classes", [])
        if isinstance(raw, str):
            classes = [c.strip().lower() for c in raw.split(",") if c.strip()]
        else:
            classes = [str(c).strip().lower() for c in (raw or [])]
        return want in classes

    # pool by spell level
    pool_by_level: DefaultDict[int, List[Mapping[str, Any]]] = defaultdict(list)
    for sp in all_spells:
        if not class_matches(sp):
            continue
        sl = _norm_level_to_int(sp.get("level", 0))
        if sl > max_lvl:
            continue
        pool_by_level[sl].append(sp)

    # stable sort: by level then name
    for sl in pool_by_level:
        pool_by_level[sl].sort(key=lambda sp: ( _norm_level_to_int(sp.get("level", 0)),
                                                str(sp.get("name","")).lower()))

    # quotas: allow override via character_data["SpellQuota"] (as strings "0","1"... or ints)
    override = character_data.get("SpellQuota", {})
    if override:
        quota: Dict[int, int] = {int(k): int(v) for k, v in override.items()}
    else:
        quota = _default_spell_quota(class_name, level, character_data)

    # selection per level according to quota
    selected: List[Mapping[str, Any]] = []
    # start from highest level down so we respect quotas for top tiers first
    for sl in sorted(quota.keys(), reverse=True):
        if sl < 0:
            continue
        need = quota.get(sl, 0)
        if need <= 0:
            continue
        available = pool_by_level.get(sl, [])
        take = min(need, len(available))
        selected.extend(available[:take])

    # If we’re short (not enough spells exist at some level), roll the remainder downwards
    total_quota = sum(max(0, v) for v in quota.values())
    if len(selected) < total_quota:
        missing = total_quota - len(selected)
        # build a fallback list of all remaining (not yet picked), highest level first
        remaining_pool: List[Tuple[int, Mapping[str, Any]]] = []
        already = {id(s) for s in selected}
        for sl in sorted(pool_by_level.keys(), reverse=True):
            for sp in pool_by_level[sl]:
                if id(sp) not in already:
                    remaining_pool.append((sl, sp))
        for _, sp in remaining_pool[:missing]:
            selected.append(sp)

    # --- build Spell1.. and flattened columns ---
    out: Dict[str, Any] = {}
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

    # pad / serialize into Spell1..Spell30 and flattened SpellN*
    for i in range(30):
        row = _row_from_spell(selected[i]) if i < len(selected) else ["","","","","",""]
        out[f"Spell{i+1}"] = row
        lvl, name, ctime, rng, crm, school = ("" if v is None else str(v) for v in (row + [""]*6)[:6])
        out[f"Spell{i+1}Level"]  = lvl
        out[f"Spell{i+1}Name"]   = name
        out[f"Spell{i+1}Time"]   = ctime
        out[f"Spell{i+1}Range"]  = rng
        out[f"Spell{i+1}CRM"]    = crm
        out[f"Spell{i+1}School"] = school

    return out
