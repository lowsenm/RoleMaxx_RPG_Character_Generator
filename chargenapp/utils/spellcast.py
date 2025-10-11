import json
import os
import random

# Load spell data
def get_spell_data():
    with open(os.path.join(os.path.dirname(__file__), "../data/spells.json"), "r", encoding="utf-8") as f:
        spells = json.load(f)
    return {spell["name"]: spell for spell in spells if "name" in spell}

# Load SRD spells
SPELL_FILE = os.path.join(os.path.dirname(__file__), "../data/spells.json")
with open(SPELL_FILE, "r", encoding="utf-8") as f:
    RAW_SPELLS = json.load(f)

# Organize spells by class and level
SPELLS = {}
for spell in RAW_SPELLS:
    level_str = spell.get("level", "")
    level = 0 if level_str.lower() == "cantrip" else int(level_str)
    name = spell.get("name", "Unknown Spell")
    school = spell.get("school", "Unknown")

    for cls in spell.get("tags", []):
        SPELLS.setdefault(cls.title(), {}).setdefault(level, []).append(name)

# Load spell slot progression
slot_file = os.path.join(os.path.dirname(__file__), "../data/spell_slots.json")
with open(slot_file, "r") as f:
    raw_slots = json.load(f)

SPELL_SLOTS = {}
for cls, slots in raw_slots.items():
    if isinstance(slots, str) and slots.startswith("same as "):
        ref_cls = slots.replace("same as ", "").strip()
        ref_data = raw_slots.get(ref_cls, {})
    else:
        ref_data = slots
    SPELL_SLOTS[cls] = {int(k): v for k, v in ref_data.items()}


def fill_spellcasting_info(char_class, character_data):
    level = int(character_data.get("Level", 1))

    # Normalize class names
    canonical_class_map = {
        "sorcerer": "Sorcerer",
        "wizard": "Wizard",
        "cleric": "Cleric",
        "bard": "Bard",
        "warlock": "Warlock",
        "paladin": "Paladin",
        "ranger": "Ranger",
        "druid": "Druid",
        "artificer": "Artificer",
    }
    char_class_key = canonical_class_map.get(char_class.lower(), char_class)

    class_spells = SPELLS.get(char_class_key, {})
    spellcasting_ability = (
        "Charisma" if char_class_key in {"Sorcerer", "Warlock", "Bard", "Paladin"} else
        "Wisdom" if char_class_key in {"Cleric", "Druid", "Ranger"} else
        "Intelligence"
    )

    # Determine available slots
    slots_by_level = {}
    if char_class_key in SPELL_SLOTS:
        sorted_lvls = sorted(SPELL_SLOTS[char_class_key].keys(), reverse=True)
        for lvl in sorted_lvls:
            if level >= lvl:
                slots_by_level = SPELL_SLOTS[char_class_key][lvl]
                break
        if not slots_by_level and sorted_lvls:
            slots_by_level = SPELL_SLOTS[char_class_key][sorted_lvls[0]]

    # Build list of chosen spells
    spell_data_map = get_spell_data()
    selected_spells = []

    for lvl in range(0, 10):
        spell_names = class_spells.get(lvl, [])
        slots = int(slots_by_level.get(str(lvl), 0)) if slots_by_level else 0
        if lvl == 0:  # cantrips
            num = 3
        else:
            num = min(slots, len(spell_names))
        if num > 0:
            chosen = random.sample(spell_names, num)
            for name in chosen:
                sdata = spell_data_map.get(name, {})
                selected_spells.append({
                    "level": str(lvl),
                    "name": name,
                    "time": sdata.get("casting_time", ""),
                    "range": sdata.get("range", ""),
                    "crms": sdata.get("components", ""),
                    "school": sdata.get("school", ""),
                    "desc": sdata.get("desc", "").replace("\n", " ")
                })

    # Build parallel lists
    Spell_Levels = [s["level"] for s in selected_spells]
    Spell_Names = [s["name"] for s in selected_spells]
    Spell_Times = [s["time"] for s in selected_spells]
    Spell_Ranges = [s["range"] for s in selected_spells]
    Spell_CRMs = [s["crms"] for s in selected_spells]
    Spell_School = [s["school"] for s in selected_spells]
    Spell_Description = [s["desc"] for s in selected_spells]

    # Add to character_data
    return {
        "SpellcastingClass": char_class_key,
        "SpellcastingAbility": spellcasting_ability,
        "Spell_Levels": "\n\n".join(Spell_Levels),
        "Spell_Names": "\n\n".join(Spell_Names),
        "Spell_Times": "\n\n".join(Spell_Times),
        "Spell_Ranges": "\n\n".join(Spell_Ranges),
        "Spell_CRMs": "\n\n".join(Spell_CRMs),
        "Spell_School": "\n\n".join(Spell_School),
        "Spell_Description": "\n\n".join(Spell_Description)
    }
