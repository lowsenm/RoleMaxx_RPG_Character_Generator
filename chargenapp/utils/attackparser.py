import json
import os
import re
from .spellcast import get_spell_data


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


def parse_attacks(character_data):
    all_attacks = []

    # --- Parse weapons from Equipment (names only) ---
    weapon_indices = character_data.get("WeaponIndices", [])

    WEAPON_BY_INDEX = build_weapon_by_index(character_data, weapon_data)

    for idx in weapon_indices:
        weapon = WEAPON_BY_INDEX.get(idx)
        if not weapon:
            print(f"Skipping weapon index {idx} — no damage info")
            continue

        if "damage" not in weapon:
            print(f"Weapon index {idx} has no damage field: {weapon.get('name', 'Unknown')}")
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

        mod = (int(character_data.get(stat, 10)) - 10) // 2
        prof_bonus = int(character_data.get("ProficiencyBonus", "+2").lstrip("+"))
        attack_bonus = mod + prof_bonus

        all_attacks.append({
            "name": weapon["name"],
            "bonus": f"+{attack_bonus}",
            "damage": f"{dmg} {dmg_type}",
            "avg": avg_dmg + attack_bonus
        })


    # --- Parse spells from all Circles and Cantrips ---
    known_spells = get_spell_data()
    known_spells = {s["name"].lower(): s for s in known_spells if "name" in s and "damage" in s}

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

    mod = (int(character_data.get(spellcasting_stat, "10")) - 10) // 2
    prof_bonus = int(character_data.get("ProficiencyBonus", "+2").lstrip("+"))
    total_bonus = mod + prof_bonus

    for i in range(10):  # Cantrips and Circle1 to Circle9
        key = "Cantrips" if i == 0 else f"Circle{i}"
        for spell in character_data.get(key, "").split("\n"):
            base = spell.split(" (")[0].strip().lower()
            if base in known_spells:
                spell_data = known_spells[base]
                dmg = spell_data["damage"]
                dtype = spell_data.get("damage_type", "varies")
                avg_dmg = average_damage(dmg)

                all_attacks.append({
                    "name": spell_data["name"],
                    "bonus": f"+{total_bonus}",
                    "damage": f"{dmg} {dtype}",
                    "avg": avg_dmg + total_bonus
                })

    # --- Sort by average damage and assign top 3 ---
    top_attacks = sorted(all_attacks, key=lambda x: -x["avg"])[:3]

    for i, atk in enumerate(top_attacks, 1):
        character_data[f"Attack{i}"] = atk["name"]
        character_data[f"AttackBonus{i}"] = atk["bonus"]
        character_data[f"Damage+Type{i}"] = atk["damage"]
#        print("AP Attacks found:", [a["name"] for a in all_attacks])
