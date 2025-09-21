import json
import os
import random


# Spell loader?
def get_spell_data():
    with open(os.path.join(os.path.dirname(__file__), "../data/spells.json"), "r", encoding="utf-8") as f:
        spells = json.load(f)
    
    # Convert list to dict: name -> spell data
    return {spell["name"]: spell for spell in spells if "name" in spell}
    
# Load raw SRD spells with metadata
spell_file = os.path.join(os.path.dirname(__file__), "../data/spells.json")
with open(spell_file, "r", encoding="utf-8") as f:
    RAW_SPELLS = json.load(f)

# Transform raw spell data into structured class/level dictionary
SPELLS = {}
for spell in RAW_SPELLS:
    level_str = spell.get("level", "")
    level = 0 if level_str.lower() == "cantrip" else int(level_str)
    school = spell.get("school", "Unknown")
    name = spell.get("name", "Unknown Spell")

    for cls in spell.get("tags", []):
        cls_title = cls.strip().title()
        SPELLS.setdefault(cls_title, {}).setdefault(level, []).append(f"{name} ({school})")

# Load spell slots from JSON
slot_file = os.path.join(os.path.dirname(__file__), "../data/spell_slots.json")
with open(slot_file, "r") as f:
    raw_slots = json.load(f)

# Define available slots
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

    # Normalize class name
    canonical_class_map = {
        "sorcerer": "Sorcerer",
        "wizard": "Wizard",
        "cleric": "Cleric",
        "bard": "Bard",
        "warlock": "Warlock",
        "paladin": "Paladin",
        "ranger": "Ranger",
        "druid": "Druid",
        "artificer": "Artificer"
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
        sorted_levels = sorted(SPELL_SLOTS[char_class_key].keys(), reverse=True)
        for lvl in sorted_levels:
            if level >= lvl:
                slots_by_level = SPELL_SLOTS[char_class_key][lvl]
                break
        if not slots_by_level and sorted_levels:
            slots_by_level = SPELL_SLOTS[char_class_key][sorted_levels[0]]


    # Define pools of high-damage cantrips per class
    top_cantrip_pool = {
        "Warlock": ["Eldritch Blast (Evocation)"],
        "Wizard": ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)", "Toll The Dead (Necromancy)", "Chill Touch (Necromancy)"],
        "Sorcerer": ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)"],
        "Cleric": ["Sacred Flame (Evocation)", "Toll The Dead (Necromancy)"],
        "Druid": ["Produce Flame (Conjuration)", "Thorn Whip (Transmutation)"]
    }

    # Pull cantrip list
    available_cantrips = class_spells.get(0, [])
    preferred_pool = top_cantrip_pool.get(char_class_key, [])

    # Filter to preferred cantrips that the class actually has access to
    valid_preferred = [spell for spell in preferred_pool if spell in available_cantrips]

    # Randomly include one preferred cantrip if available
    cantrips = set()
    if valid_preferred:
        cantrips.add(random.choice(valid_preferred))

    # Fill remaining cantrips randomly
    remaining_choices = [spell for spell in available_cantrips if spell not in cantrips]
    cantrips.update(random.sample(remaining_choices, min(3 - len(cantrips), len(remaining_choices))))

        # Compute spellcasting stats
    prof_bonus = int(character_data.get("ProficiencyBonus", 2))
    ability_mod = int(character_data.get(spellcasting_ability, 10))
    ability_modifier = (ability_mod - 10) // 2

    spell_save_dc = 8 + prof_bonus + ability_modifier
    spell_attack_bonus = prof_bonus + ability_modifier

    spellcasting_info = {
        "SpellcastingClass": char_class_key,
        "SpellcastingAbility": spellcasting_ability,
        "SpellSaveDC": str(spell_save_dc),
        "SpellAttackBonus": f"+{spell_attack_bonus}" if spell_attack_bonus >= 0 else str(spell_attack_bonus),
        "Cantrips": "\n".join(sorted(cantrips))
    }

    for circle in range(1, 10):
        key_circle = f"Circle{circle}"
        key_slots = f"Slots{circle}"
        key_exp = f"Exp{circle}"
        spells = class_spells.get(circle, [])
        slots = slots_by_level.get(str(circle), 0)

        if slots > 0 and spells:
            known_spells = random.sample(spells, min(slots, len(spells)))
            spellcasting_info[key_circle] = "\n".join(known_spells)
            spellcasting_info[key_slots] = str(slots)
            spellcasting_info[key_exp] = ""
        else:
            spellcasting_info[key_circle] = ""
            spellcasting_info[key_slots] = ""
            spellcasting_info[key_exp] = ""

    spellcasting_info["Exp1"] = spellcasting_info.get("Exp1", "")
    spellcasting_info["Circle1"] = spellcasting_info.get("Circle1", "")

    return spellcasting_info
