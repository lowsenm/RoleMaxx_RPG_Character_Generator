import json
import os
import re
from .spellcast import _load_spells_default


# Load weapon data
#with open(os.path.join(os.path.dirname(__file__), "../data/weapons.json"), "r", encoding="utf-8") as f:
#    weapon_data = json.load(f)    
#damage_list = {weapon_data[str(item)]["damage"] for item in weaponlist}


# Load weapon data as a dict of dicts
with open(os.path.join(os.path.dirname(__file__), "../data/weapons.json"), "r", encoding="utf-8") as f:
    weapon_data = json.load(f)

# Ensure keys are integers if they were stored as strings
weapon_data = {int(k): v for k, v in weapon_data.items()}


def build_weapon_by_index(character_data, weapon_data):
    """
    Build WEAPON_BY_INDEX dict using only the indices in character_data["WeaponsIndices"].
    Each entry will include name and damage.
    """
    weapon_indices = character_data.get("WeaponIndices", [])

    weapon_by_index = {}

    for idx in weapon_indices:
        weapon = weapon_data.get(idx)
        if not weapon:
            print(f"⚠️ Weapon index {idx} not found in weapon_data.")
            continue

        # Check for required fields
        if "name" not in weapon or "damage" not in weapon or "damage_dice" not in weapon["damage"] or "damage_type" not in weapon["damage"]:
            print(f"⚠️ Incomplete damage info for weapon at index {idx}. Skipping.")
            continue

        # Build entry
        weapon_by_index[idx] = {
            "name": weapon["name"],
            "damage": weapon["damage"]  # ← leave it as a dict
        }

    return weapon_by_index

def average_damage(damage_str):
    """Compute expected average for a damage dice string like '1d8' or '2d6'."""
    try:
        match = re.match(r"(\d+)d(\d+)", damage_str.lower())
        if match:
            count, size = map(int, match.groups())
            return (count * (1 + size)) / 2
    except:
        pass
    return 0


import re

def average_damage(damage_str: str) -> float:
    """
    Expected average across ANY number of dice groups in a string.
    e.g., '2d6', '1d8 + 1d6', '2d6+3' (flat +N is ignored for avg).
    """
    if not damage_str:
        return 0.0
    total = 0.0
    for count, size in re.findall(r"(\d+)\s*d\s*(\d+)", damage_str.lower()):
        c, s = int(count), int(size)
        total += c * (1 + s) / 2
    return total

def _get_spell_damage_and_type(sdata: dict) -> tuple[str, str]:
    """
    Try several common schemas for spell damage payloads and return (dice_str, type_name).
    """
    # 1) Flat string fields commonly used in homebrew datasets
    if isinstance(sdata.get("damage"), str):
        return sdata["damage"], sdata.get("damage_type", "varies")

    # 2) 5e-API-like: damage = {"damage_dice":"1d10","damage_type":{"name":"fire"}}
    dmg = sdata.get("damage") or {}
    if isinstance(dmg, dict) and "damage_dice" in dmg:
        dtype = dmg.get("damage_type", {})
        if isinstance(dtype, dict):
            dtype = dtype.get("name", "varies")
        return dmg["damage_dice"], dtype or "varies"

    # 3) Sometimes datasets store top-level fields
    if "damage_dice" in sdata:
        dtype = sdata.get("damage_type", {})
        if isinstance(dtype, dict):
            dtype = dtype.get("name", "varies")
        elif not isinstance(dtype, str):
            dtype = "varies"
        return sdata["damage_dice"], dtype

    return "", ""


def parse_attacks(character_data):
    """
    Build top-3 attacks with these guarantees:
      • Include at least one cantrip if any are known.
      • If the character is a spellcaster and has only ONE weapon, include at least two cantrips (when available).

    Now reads spells from flat fields: Spell1Name/Spell1Level ... Spell30Name/Spell30Level.
    """

    # -----------------------
    # Helpers / lookups
    # -----------------------
    def is_spellcaster(cls: str) -> bool:
        return (cls or "").strip().lower() in {
            "bard","cleric","druid","sorcerer","warlock","wizard","paladin","ranger","artificer"
        }

    def prof_bonus_from_str(x, default=2):
        try:
            return int(str(x).lstrip("+"))
        except Exception:
            try:
                lvl = int(character_data.get("Level", 1))
            except Exception:
                lvl = 1
            if lvl <= 4: return 2
            if lvl <= 8: return 3
            if lvl <= 12: return 4
            if lvl <= 16: return 5
            return 6

    def ability_mod(score_like, default_score=10):
        try:
            s = int(score_like)
        except Exception:
            s = default_score
        return (s - 10) // 2

    # -----------------------
    # Collect WEAPON attacks (unchanged)
    # -----------------------
    all_attacks = []
    weapon_indices = character_data.get("WeaponIndices", []) or []
    WEAPON_BY_INDEX = build_weapon_by_index(character_data, weapon_data)

    for idx in weapon_indices:
        weapon = WEAPON_BY_INDEX.get(idx)
        if not weapon or "damage" not in weapon:
            continue

        dmg = weapon["damage"]["damage_dice"]
        dmg_type = weapon["damage"]["damage_type"]["name"]
        avg_dmg = average_damage(dmg)

        properties = [p["index"] for p in weapon.get("properties", [])]
        str_score = int(character_data.get("Strength", "10"))
        dex_score = int(character_data.get("Dexterity", "10"))

        if "finesse" in properties:
            stat = "Dexterity" if dex_score >= str_score else "Strength"
        elif weapon.get("weapon_range") == "Ranged":
            stat = "Dexterity"
        else:
            stat = "Strength"

        mod = ability_mod(character_data.get(stat, 10))
        prof_bonus = prof_bonus_from_str(character_data.get("ProficiencyBonus", "+2"))
        attack_bonus = mod + prof_bonus

        all_attacks.append({
            "name": weapon["name"],
            "bonus": f"+{attack_bonus}",
            "damage": f"{dmg} {dmg_type}",
            "avg": avg_dmg + attack_bonus,
            "is_cantrip": False,
            "kind": "weapon",
        })

    weapon_count = len([a for a in all_attacks if a["kind"] == "weapon"])

    # -----------------------
    # Collect SPELL attacks from FLAT fields
    # -----------------------
    # Load spell reference data
    _spells_raw = _load_spells_default()
    if isinstance(_spells_raw, dict):
        spell_lookup = {k.lower(): v for k, v in _spells_raw.items()}
    else:
        spell_lookup = {s["name"].lower(): s for s in (_spells_raw or []) if isinstance(s, dict) and "name" in s}

    # Determine spellcasting ability
    spellcasting_stat = {
        "Bard": "Charisma",
        "Cleric": "Wisdom",
        "Druid": "Wisdom",
        "Sorcerer": "Charisma",
        "Warlock": "Charisma",
        "Wizard": "Intelligence",
        "Paladin": "Charisma",
        "Ranger": "Wisdom",
        "Artificer": "Intelligence"
    }.get(character_data.get("Class", ""), "Intelligence")

    sc_mod = ability_mod(character_data.get(spellcasting_stat, "10"))
    prof_bonus = prof_bonus_from_str(character_data.get("ProficiencyBonus", "+2"))
    total_bonus = sc_mod + prof_bonus

    cantrip_attacks = []
    leveled_attacks = []

    # Walk Spell1..Spell30
    for i in range(1, 31):
        name = (character_data.get(f"Spell{i}Name", "") or "").strip()
        if not name:
            continue
        lvl_raw = (character_data.get(f"Spell{i}Level", "") or "").strip().lower()
        try:
            lvl = int(lvl_raw) if lvl_raw != "" else None
        except ValueError:
            # sometimes "cantrip" or text
            lvl = 0 if "cantrip" in lvl_raw else None

        sdata = spell_lookup.get(name.lower())
        if not sdata:
            continue

        # If level missing in flat fields, fall back to spell DB if it has it
        if lvl is None:
            sp_l = sdata.get("level", 0)
            try:
                lvl = int(sp_l)
            except Exception:
                lvl = 0  # assume cantrip if unknown

        dmg_dice, dmg_type = _get_spell_damage_and_type(sdata)
        if not dmg_dice:
            # non-damaging spell; skip for "top attacks" purposes
            continue

        avg_dmg = average_damage(dmg_dice)
        entry = {
            "name": sdata.get("name", name),
            "bonus": f"+{total_bonus}",
            "damage": f"{dmg_dice} {dmg_type or 'varies'}",
            "avg": avg_dmg + total_bonus,
            "is_cantrip": (lvl == 0),
            "kind": "spell",
        }
        if entry["is_cantrip"]:
            cantrip_attacks.append(entry)
        else:
            leveled_attacks.append(entry)

    # Merge into all_attacks
    all_attacks.extend(cantrip_attacks)
    all_attacks.extend(leveled_attacks)

    # -----------------------
    # Selection with cantrip guarantees
    # -----------------------
    cantrip_attacks.sort(key=lambda x: -x["avg"])
    weapon_attacks = [a for a in all_attacks if a["kind"] == "weapon"]
    weapon_attacks.sort(key=lambda x: -x["avg"])
    non_cantrip_spell_attacks = [a for a in all_attacks if (a["kind"] == "spell" and not a["is_cantrip"])]
    non_cantrip_spell_attacks.sort(key=lambda x: -x["avg"])

    # Decide cantrip quota
    knows_cantrip = len(cantrip_attacks) > 0
    desired_cantrips = 0
    if knows_cantrip:
        desired_cantrips = 1
        if is_spellcaster(character_data.get("Class", "")) and weapon_count == 1:
            desired_cantrips = 2
        desired_cantrips = min(desired_cantrips, len(cantrip_attacks))

    picked = []
    used_names = set()

    # a) take required cantrips first
    for c in cantrip_attacks[:desired_cantrips]:
        picked.append(c)
        used_names.add(c["name"])

    # b) fill remaining slots (to 3) from the best of the rest
    def add_from_pool(pool):
        nonlocal picked, used_names
        for item in pool:
            if len(picked) >= 3:
                break
            if item["name"] in used_names:
                continue
            picked.append(item)
            used_names.add(item["name"])

    # Choose priority: weapons > leveled spells > extra cantrips
    add_from_pool(weapon_attacks)
    add_from_pool(non_cantrip_spell_attacks)
    add_from_pool(cantrip_attacks[desired_cantrips:])

    # Safety pad
    if len(picked) < 3:
        leftovers = [a for a in (weapon_attacks + non_cantrip_spell_attacks + cantrip_attacks)
                     if a["name"] not in used_names]
        leftovers.sort(key=lambda x: -x["avg"])
        add_from_pool(leftovers)

    top_attacks = picked[:3]

    # -----------------------
    # Write back to character_data
    # -----------------------
    for i, atk in enumerate(top_attacks, 1):
        character_data[f"Attack{i}"] = atk["name"]
        character_data[f"AttackBonus{i}"] = atk["bonus"]
        character_data[f"Damage+Type{i}"] = atk["damage"]
