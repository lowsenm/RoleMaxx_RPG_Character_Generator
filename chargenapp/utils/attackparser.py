import json, os
import re
from .spellcast import _load_spells_default
import json, os, re
from typing import Dict, Any, List, Tuple, Optional


SPELLCASTING_CLASSES = {"Sorcerer","Warlock","Wizard","Artificer"} # Those relying on spells for damage

_dice_re = re.compile(r"^\s*(\d+)\s*[dD]\s*(\d+)\s*$")

def _exp(d): 
    m = _dice_re.match(d or "")
    return (int(m.group(1)) * (int(m.group(2)) + 1) / 2.0) if m else 0.0

def parse_attacks(character_data):
    # Load data
    wpnidx = character_data.get("WeaponIndices", [])
    path = os.path.join(os.path.dirname(__file__), "../data/weapons.json")

    with open(path, encoding="utf-8") as f:
        weapons = json.load(f)  # dict like {"64": {...}, "12": {...}, ...}

    # Create weaps dict with top 3 weapons in order
    wpndict = [
        {
            "index": idx,
            "name": weapons[str(idx)]["name"],
            "damage_dice": ((weapons[str(idx)].get("damage") or {}).get("damage_dice") or ""),
        }
        for idx in wpnidx
        if str(idx) in weapons
    ]
    wpndict.sort(key=lambda w: _exp(w.get("damage_dice", "")), reverse=True)
    print(wpndict)

    # If not spellcaster, load spell data and return top attack plus most damaging spell & cantrip (3 total) 
    cls = str(character_data.get("Class", "")).strip().title()
    if cls not in SPELLCASTING_CLASSES:
        for i, w in enumerate(wpndict[:3], start=1):
            character_data[f"Attack{i}"] = w.get("name", "—")
            character_data[f"AttackBonus{i}"] = ""  # no bonus in wpndict; leave blank or compute elsewhere
            character_data[f"Damage+Type{i}"] = w.get("damage_dice", "")
    else:
        top_spell_candidates = character_data.get("SpellCandidates")
        for i, pick in enumerate(top_spell_candidates[:3], start=1): # Load 1 cantrip, 1 spell
            character_data[f"Attack{i}"] = pick.get("name", "—")
            character_data[f"AttackBonus{i}"] = character_data.get("SpellAttackBonus", "")
            character_data[f"Damage+Type{i}"] = pick.get("damage_dice", "")
        pick = wpndict[0] if wpndict else {} #Load 1 weapon
        character_data[f"Attack3"] = pick.get("name", "—")
        character_data[f"AttackBonus3"] = character_data.get("ProficiencyBonus", "")
        character_data[f"Damage+Type3"] = pick.get("damage_dice", "")

    return character_data
