# Stat generation
import random

# 5e standard classes and their primary abilities
CLASS_PRIORITIES = {
    "Barbarian": ["Strength", "Constitution"],
    "Bard": ["Charisma", "Dexterity"],
    "Cleric": ["Wisdom", "Strength"],
    "Druid": ["Wisdom", "Constitution"],
    "Fighter": ["Strength", "Constitution"],
    "Monk": ["Dexterity", "Wisdom"],
    "Paladin": ["Strength", "Charisma"],
    "Ranger": ["Dexterity", "Wisdom"],
    "Rogue": ["Dexterity", "Intelligence"],
    "Sorcerer": ["Charisma", "Constitution"],
    "Warlock": ["Charisma", "Wisdom"],
    "Wizard": ["Intelligence", "Dexterity"]
}

# Racial bonuses for core races (5e)
RACE_BONUSES = {
    "Human": {"Strength": 1, "Dexterity": 1, "Constitution": 1, "Intelligence": 1, "Wisdom": 1, "Charisma": 1},
    "Elf": {"Dexterity": 2},
    "Dwarf": {"Constitution": 2},
    "Halfling": {"Dexterity": 2},
    "Half-Orc": {"Strength": 2, "Constitution": 1},
    "Gnome": {"Intelligence": 2},
    "Half-Elf": {"Charisma": 2},
    "Tiefling": {"Charisma": 2, "Intelligence": 1},
    "Dragonborn": {"Strength": 2, "Charisma": 1}
}

# XP thresholds based on D&D 5e progression
XP_THRESHOLDS = [
    0, 300, 900, 2700, 6500,
    14000, 23000, 34000, 48000, 64000,
    85000, 100000, 120000, 140000, 165000,
    195000, 225000, 265000, 305000, 355000,
    410000, 470000, 535000, 605000, 680000, 
    760000, 845000, 935000, 1030000, 1135000
]

def roll_stat():
    """Roll 4d6 and drop the lowest."""
    rolls = sorted([random.randint(1, 6) for _ in range(4)])
    return sum(rolls[1:])

def generate_base_stats():
    """Roll six ability scores."""
    return sorted([roll_stat() for _ in range(6)], reverse=True)

def apply_racial_bonuses(stats, race):
    """Apply racial bonuses to the stats dictionary."""
    STAT_NAMES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    bonuses = RACE_BONUSES.get(race, {})
    for stat in bonuses:
        stats[stat] += bonuses[stat]

    # Special case: Half-Elf chooses 2 other stats for +1
    if race == "Half-Elf":
        choices = [s for s in STAT_NAMES if s != "Charisma"]
        random.shuffle(choices)
        stats[choices[0]] += 1
        stats[choices[1]] += 1
    return stats

def assign_stats_to_class(raw_stats, char_class):
    """Assign rolled stats to attributes based on class priority."""
    STAT_NAMES = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
    stat_order = CLASS_PRIORITIES.get(char_class, STAT_NAMES)
    assigned_stats = {}
    for i, stat in enumerate(stat_order):
        assigned_stats[stat] = raw_stats[i]

    remaining = [s for s in STAT_NAMES if s not in assigned_stats]
    for i, stat in enumerate(remaining):
        assigned_stats[stat] = raw_stats[len(stat_order) + i]

    return assigned_stats

def apply_level_up_bonuses(stats, char_class, level):
    """Apply ASIs (Ability Score Improvements) for a given level."""
    num_asis = sum(1 for lvl in [4, 8, 12, 16, 19] if level >= lvl)
    primary_stats = CLASS_PRIORITIES.get(char_class, ["Strength", "Dexterity"])
    for _ in range(num_asis * 2):  # 2 points per ASI
        stat = random.choice(primary_stats)
        stats[stat] += 1
    return stats

def generate_random_xp(level):
    """Generate XP randomly within the level's threshold range."""
    if level < 1 or level > 30:
        raise ValueError("Level must be between 1 and 30.")
    if level == 1: #starts level 1 characters at 0 xp
        return 0
    else:
        low = XP_THRESHOLDS[level - 1]
        high = XP_THRESHOLDS[level] - 1 if level < 30 else XP_THRESHOLDS[level - 1] + 50000
        return random.randint(low, high)

def generate_character_stats(race, char_class, level):
    """Generate full character stats for a given race, class, and level."""
    raw_stats = generate_base_stats()
    assigned = assign_stats_to_class(raw_stats, char_class)
    with_race = apply_racial_bonuses(assigned, race)
    leveled_up = apply_level_up_bonuses(with_race, char_class, level)
    xp = generate_random_xp(level)
    return {"stats": leveled_up, "level": str(level), "XP": str(xp)}
