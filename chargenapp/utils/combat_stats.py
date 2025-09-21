def calculate_combat_stats(character_data):
    """
    Calculates and fills in core combat stats in character_data:
    HitDice, HPMax, ProficiencyBonus, AC, Speed.
    """
    import math
    import re

    # --- Get core values ---
    char_class = character_data.get("Class", "").lower()
    race = character_data.get("Race", "").lower()
    level = int(character_data.get("Level", "1"))
    con_score = int(character_data.get("Constitution", 10))
    dex_score = int(character_data.get("Dexterity", 10))
    equipment = character_data.get("EquipmentCB", "").lower()

    # --- Calculate modifiers ---
    con_mod = (con_score - 10) // 2
    dex_mod = (dex_score - 10) // 2

    # --- Hit Dice ---
    hit_die_by_class = {
        "barbarian": 12,
        "fighter": 10,
        "paladin": 10,
        "ranger": 10,
        "bard": 8,
        "cleric": 8,
        "druid": 8,
        "monk": 8,
        "rogue": 8,
        "warlock": 8,
        "sorcerer": 6,
        "wizard": 6,
        "artificer": 8
    }
    hit_die = hit_die_by_class.get(char_class, 8)
    character_data["HitDice"] = f"{level}d{hit_die}"

    # --- HP Max (Average) ---
    first_level_hp = hit_die + con_mod
    additional_levels_hp = (level - 1) * ((hit_die // 2 + 1) + con_mod)
    total_hp = first_level_hp + additional_levels_hp
    character_data["HPMax"] = str(total_hp)

    # --- Proficiency Bonus ---
    prof_bonus = 2 + ((level - 1) // 4)
    character_data["ProficiencyBonus"] = f"+{prof_bonus}"

    # --- Armor Lookup Table ---
    armor_table = {
        "padded armor":      {"base": 11, "max_dex": None},
        "leather armor":     {"base": 11, "max_dex": None},
        "studded leather":   {"base": 12, "max_dex": None},
        "hide armor":        {"base": 12, "max_dex": 2},
        "chain shirt":       {"base": 13, "max_dex": 2},
        "scale mail":        {"base": 14, "max_dex": 2},
        "breastplate":       {"base": 14, "max_dex": 2},
        "half plate":        {"base": 15, "max_dex": 2},
        "ring mail":         {"base": 14, "max_dex": 0},
        "chain mail":        {"base": 16, "max_dex": 0},
        "splint":            {"base": 17, "max_dex": 0},
        "plate":             {"base": 18, "max_dex": 0},
        "unarmored":         {"base": 10, "max_dex": None}
    }

    # --- Detect armor in equipment ---
    equipped_armor = "unarmored"
    for armor in armor_table:
        if armor in equipment:
            equipped_armor = armor
            break

    armor_info = armor_table[equipped_armor]
    dex_for_ac = dex_mod
    if armor_info["max_dex"] is not None:
        dex_for_ac = min(dex_mod, armor_info["max_dex"])
    ac = armor_info["base"] + dex_for_ac
    character_data["AC"] = str(ac)

    # --- Speed by Race ---
    speed_by_race = {
        "dwarf": 25,
        "halfling": 25,
        "gnome": 25,
        "human": 30,
        "elf": 30,
        "half-elf": 30,
        "half-orc": 30,
        "dragonborn": 30,
        "tiefling": 30
    }
    character_data["Speed"] = str(speed_by_race.get(race, 30))
