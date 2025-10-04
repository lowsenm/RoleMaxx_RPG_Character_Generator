import json
import os
import random


# Spell loader
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
        "artificer": "Artificer",
    }
    char_class_key = canonical_class_map.get(char_class.lower(), char_class)

    class_spells = SPELLS.get(char_class_key, {})
    spellcasting_ability = (
        "Charisma" if char_class_key in {"Sorcerer", "Warlock", "Bard", "Paladin"} else
        "Wisdom"   if char_class_key in {"Cleric", "Druid", "Ranger"} else
        "Intelligence"
    )

    # Determine available spell slots
    slots_by_level = {}
    if char_class_key in SPELL_SLOTS:
        sorted_levels = sorted(SPELL_SLOTS[char_class_key].keys(), reverse=True)
        for lvl in sorted_levels:
            if level >= lvl:
                slots_by_level = SPELL_SLOTS[char_class_key][lvl]
                break
        if not slots_by_level and sorted_levels:
            slots_by_level = SPELL_SLOTS[char_class_key][sorted_levels[0]]

    # Preferred cantrips
    top_cantrip_pool = {
        "Warlock":   ["Eldritch Blast (Evocation)"],
        "Wizard":    ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)", "Toll The Dead (Necromancy)", "Chill Touch (Necromancy)"],
        "Sorcerer":  ["Fire Bolt (Evocation)", "Ray Of Frost (Evocation)"],
        "Cleric":    ["Sacred Flame (Evocation)", "Toll The Dead (Necromancy)"],
        "Druid":     ["Produce Flame (Conjuration)", "Thorn Whip (Transmutation)"],
    }

    available_cantrips = class_spells.get(0, [])
    preferred_pool = top_cantrip_pool.get(char_class_key, [])
    valid_preferred = [s for s in preferred_pool if s in available_cantrips]

    cantrips = set()
    if valid_preferred:
        cantrips.add(random.choice(valid_preferred))

    remaining_cantrips = [s for s in available_cantrips if s not in cantrips]
    cantrips.update(random.sample(remaining_cantrips, min(3 - len(cantrips), len(remaining_cantrips))))

    # Spellcasting stats
    prof_bonus = int(character_data.get("ProficiencyBonus", 2))
    ability_score = int(character_data.get(spellcasting_ability, 10))
    ability_mod = (ability_score - 10) // 2
    spell_save_dc = 8 + prof_bonus + ability_mod
    spell_attack_bonus = prof_bonus + ability_mod

    # Build properly structured spell list
    all_spells = []

    # Cantrips
    for spell in sorted(cantrips):
        # Example: "Fire Bolt (Evocation)"
        if "(" in spell and spell.endswith(")"):
            name, school = spell[:-1].split(" (")
        else:
            name, school = spell, "Unknown"
        all_spells.append((0, name.strip(), school.strip()))

    # Higher-level spells
    for circle in range(1, 10):
        spells_at_level = class_spells.get(circle, [])
        slots = int(slots_by_level.get(str(circle), 0)) if slots_by_level else 0
        if slots > 0 and spells_at_level:
            known_spells = random.sample(spells_at_level, min(slots, len(spells_at_level)))
            for spell in known_spells:
                if "(" in spell and spell.endswith(")"):
                    name, school = spell[:-1].split(" (")
                else:
                    name, school = spell, "Unknown"
                all_spells.append((circle, name.strip(), school.strip()))

    # Format into tab- and line-separated list
    formatted_spells = "\n".join(f"{circle}\t{name}\t{school}" for (circle, name, school) in all_spells)

    return {
        "SpellcastingClass": char_class_key,
        "SpellcastingAbility": spellcasting_ability,
        "SpellSaveDC": str(spell_save_dc),
        "SpellAttackBonus": f"+{spell_attack_bonus}" if spell_attack_bonus >= 0 else str(spell_attack_bonus),
        "Spells": formatted_spells
    }
